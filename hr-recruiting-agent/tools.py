"""أدوات منسق التوظيف: قراءة وتعديل بيانات الوظائف والمرشحين والمواعيد.

البيانات محفوظة في ملفات JSON داخل مجلد data/ — تقدر تستبدلها لاحقاً
بنظام ATS أو Google Sheets بدون ما تغيّر الوكيل نفسه.
"""

import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTBOX_DIR = BASE_DIR / "outbox"

STATUSES = ["new", "screening", "interview_scheduled", "interviewed", "offer", "hired", "rejected"]
EMAIL_TYPES = ["interview_invitation", "reschedule", "rejection", "offer", "follow_up", "hiring_manager_update"]


def _load(name):
    return json.loads((DATA_DIR / f"{name}.json").read_text(encoding="utf-8"))


def _save(name, data):
    (DATA_DIR / f"{name}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _find(items, item_id, label):
    for item in items:
        if item["id"] == item_id:
            return item
    raise ValueError(f"{label} غير موجود: {item_id}")


# ---------- تنفيذ الأدوات ----------

def list_jobs():
    return _load("jobs")


def list_candidates(job_id, status):
    candidates = _load("candidates")
    if job_id:
        candidates = [c for c in candidates if c["job_id"] == job_id]
    if status:
        candidates = [c for c in candidates if c["status"] == status]
    return [
        {k: c[k] for k in ("id", "name", "job_id", "status", "years_experience", "summary")}
        for c in candidates
    ]


def get_candidate(candidate_id):
    return _find(_load("candidates"), candidate_id, "المرشح")


def update_candidate_status(candidate_id, status, note):
    candidates = _load("candidates")
    candidate = _find(candidates, candidate_id, "المرشح")
    old = candidate["status"]
    candidate["status"] = status
    if note:
        candidate["notes"].append({"at": datetime.now().isoformat(timespec="minutes"), "text": note})
    _save("candidates", candidates)
    return {"candidate_id": candidate_id, "old_status": old, "new_status": status}


def list_available_slots(date):
    slots = [s for s in _load("slots") if s["booked_by"] is None]
    if date:
        slots = [s for s in slots if s["start"].startswith(date)]
    return slots


def book_interview(candidate_id, slot_id, interviewers):
    candidates = _load("candidates")
    slots = _load("slots")
    candidate = _find(candidates, candidate_id, "المرشح")
    slot = _find(slots, slot_id, "الموعد")
    if slot["booked_by"] is not None:
        raise ValueError(f"الموعد {slot_id} محجوز مسبقاً")
    if candidate["interview"]:
        raise ValueError(f"المرشح عنده مقابلة محجوزة ({candidate['interview']['slot_id']}). ألغها أولاً.")
    slot["booked_by"] = candidate_id
    candidate["interview"] = {
        "slot_id": slot_id,
        "start": slot["start"],
        "duration_minutes": slot["duration_minutes"],
        "mode": slot["mode"],
        "interviewers": interviewers,
    }
    candidate["status"] = "interview_scheduled"
    _save("slots", slots)
    _save("candidates", candidates)
    return {"booked": True, "candidate": candidate["name"], **candidate["interview"]}


def cancel_interview(candidate_id, reason):
    candidates = _load("candidates")
    slots = _load("slots")
    candidate = _find(candidates, candidate_id, "المرشح")
    if not candidate["interview"]:
        raise ValueError("ما فيه مقابلة محجوزة لهذا المرشح")
    slot = _find(slots, candidate["interview"]["slot_id"], "الموعد")
    slot["booked_by"] = None
    candidate["interview"] = None
    candidate["status"] = "screening"
    candidate["notes"].append({"at": datetime.now().isoformat(timespec="minutes"), "text": f"إلغاء مقابلة: {reason}"})
    _save("slots", slots)
    _save("candidates", candidates)
    return {"cancelled": True, "slot_released": slot["id"]}


def draft_email(to, email_type, subject, body):
    """يحفظ الإيميل كمسودة في outbox/ — ما يُرسل أي شي بدون مراجعة بشرية."""
    OUTBOX_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    path = OUTBOX_DIR / f"{stamp}_{email_type}.md"
    path.write_text(
        f"**إلى:** {to}\n**النوع:** {email_type}\n**الموضوع:** {subject}\n\n---\n\n{body}\n",
        encoding="utf-8",
    )
    return {"saved_as_draft": str(path.relative_to(BASE_DIR)), "sent": False}


# ---------- تعريفات الأدوات لـ Claude ----------

def _schema(properties, required=None):
    return {
        "type": "object",
        "properties": properties,
        "required": required if required is not None else list(properties),
        "additionalProperties": False,
    }


NULLABLE_STR = {"type": ["string", "null"]}

TOOL_DEFINITIONS = [
    {
        "name": "list_jobs",
        "description": "يعرض الوظائف الشاغرة مع متطلباتها ومدير التوظيف لكل وظيفة.",
        "input_schema": _schema({}),
    },
    {
        "name": "list_candidates",
        "description": "يعرض المرشحين، مع فلترة اختيارية حسب الوظيفة أو الحالة. مرّر null لتجاهل الفلتر.",
        "input_schema": _schema({
            "job_id": {**NULLABLE_STR, "description": "رقم الوظيفة مثل JOB-001 أو null"},
            "status": {**NULLABLE_STR, "description": f"حالة المرشح ({' / '.join(STATUSES)}) أو null"},
        }),
    },
    {
        "name": "get_candidate",
        "description": "يعرض الملف الكامل لمرشح: التواصل، الملخص، الملاحظات، والمقابلة إن وجدت.",
        "input_schema": _schema({"candidate_id": {"type": "string"}}),
    },
    {
        "name": "update_candidate_status",
        "description": "يغيّر حالة المرشح في مسار التوظيف ويضيف ملاحظة اختيارية.",
        "input_schema": _schema({
            "candidate_id": {"type": "string"},
            "status": {"type": "string", "enum": STATUSES},
            "note": {**NULLABLE_STR, "description": "سبب التغيير أو ملاحظة، أو null"},
        }),
    },
    {
        "name": "list_available_slots",
        "description": "يعرض مواعيد المقابلات المتاحة (غير المحجوزة). التاريخ بصيغة YYYY-MM-DD أو null لكل المواعيد.",
        "input_schema": _schema({"date": NULLABLE_STR}),
    },
    {
        "name": "book_interview",
        "description": "يحجز موعد مقابلة لمرشح ويغيّر حالته إلى interview_scheduled. لا يرسل دعوة؛ استخدم draft_email بعدها.",
        "input_schema": _schema({
            "candidate_id": {"type": "string"},
            "slot_id": {"type": "string"},
            "interviewers": {"type": "array", "items": {"type": "string"}, "description": "أسماء من سيجري المقابلة"},
        }),
    },
    {
        "name": "cancel_interview",
        "description": "يلغي مقابلة المرشح ويحرر الموعد ويرجع حالته إلى screening.",
        "input_schema": _schema({"candidate_id": {"type": "string"}, "reason": {"type": "string"}}),
    },
    {
        "name": "draft_email",
        "description": "يكتب مسودة إيميل ويحفظها في مجلد outbox لمراجعة فريق الموارد البشرية. لا يرسل الإيميل.",
        "input_schema": _schema({
            "to": {"type": "string", "description": "البريد الإلكتروني للمستلم"},
            "email_type": {"type": "string", "enum": EMAIL_TYPES},
            "subject": {"type": "string"},
            "body": {"type": "string"},
        }),
    },
]

TOOLS = [{**t, "strict": True} for t in TOOL_DEFINITIONS]

HANDLERS = {
    "list_jobs": list_jobs,
    "list_candidates": list_candidates,
    "get_candidate": get_candidate,
    "update_candidate_status": update_candidate_status,
    "list_available_slots": list_available_slots,
    "book_interview": book_interview,
    "cancel_interview": cancel_interview,
    "draft_email": draft_email,
}


def run_tool(name, tool_input):
    """ينفذ الأداة ويرجع (النتيجة كنص JSON، هل هي خطأ)."""
    try:
        result = HANDLERS[name](**tool_input)
        return json.dumps(result, ensure_ascii=False), False
    except (ValueError, KeyError, TypeError) as e:
        return f"خطأ: {e}", True
