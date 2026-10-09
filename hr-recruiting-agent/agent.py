"""منسق التوظيف — وكيل ذكاء اصطناعي لفريق الموارد البشرية.

التشغيل:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=...
    python agent.py
"""

from datetime import date

import anthropic

from tools import TOOLS, run_tool

MODEL = "claude-opus-5-5"

SYSTEM_PROMPT = f"""أنت "منسق التوظيف"، مساعد لفريق الموارد البشرية في شركة سعودية.

مهامك:
- متابعة المرشحين في مسار التوظيف وتحديث حالاتهم.
- اقتراح وحجز مواعيد المقابلات من المواعيد المتاحة فقط.
- كتابة مسودات إيميلات احترافية للمرشحين ومديري التوظيف (دعوة مقابلة، إعادة جدولة، اعتذار، عرض وظيفي، متابعة).
- مقارنة المرشحين بمتطلبات الوظيفة وإعطاء توصية مختصرة ومبررة.

قواعد العمل:
- استخدم الأدوات للحصول على البيانات؛ لا تخترع مرشحين أو مواعيد أو معلومات غير موجودة.
- الإيميلات تُحفظ كمسودات فقط ويراجعها الفريق قبل الإرسال. بعد كل مسودة اذكر مسار الملف.
- قبل الإجراءات اللي يصعب التراجع عنها (رفض مرشح، إرسال عرض وظيفي، إلغاء مقابلة) اعرض ما ستفعله واطلب تأكيد المستخدم، إلا إذا طلبها صراحة.
- قيّم المرشحين على أساس المؤهلات والخبرة المرتبطة بالوظيفة فقط، وتجاهل العمر والجنس والجنسية والحالة الاجتماعية وأي سمة غير مهنية.
- رد بلغة المستخدم (العربية افتراضياً) وبأسلوب مهني مختصر. اكتب الإيميلات بالعربية الفصحى المهنية ما لم يُطلب غير ذلك.
- عند حجز مقابلة، اكتب بعدها مسودة دعوة للمرشح فيها الموعد وطريقة المقابلة.

تاريخ اليوم: {date.today().isoformat()}"""


def chat_turn(client, messages):
    """يكمل دورة واحدة: يستدعي Claude وينفذ الأدوات حتى ينتهي من الرد."""
    while True:
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
            output_config={"effort": "medium"},
            # لو رفضت مصنّفات الأمان الطلب، يُعاد تلقائياً على نموذج بديل
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "refusal":
            return "تعذّر إكمال هذا الطلب. جرّب صياغته بشكل مختلف."

        tool_uses = [b for b in response.content if b.type == "tool_use"]
        if response.stop_reason != "tool_use" or not tool_uses:
            text = "\n".join(b.text for b in response.content if b.type == "text")
            if response.stop_reason == "max_tokens":
                text += "\n\n(تم قطع الرد لأنه طويل جداً)"
            return text

        results = []
        for block in tool_uses:
            print(f"  ⚙️  {block.name}")
            content, is_error = run_tool(block.name, block.input)
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": content,
                "is_error": is_error,
            })
        messages.append({"role": "user", "content": results})


def main():
    client = anthropic.Anthropic()
    messages = []
    print("منسق التوظيف جاهز 👋  (اكتب 'خروج' للإنهاء)\n")
    while True:
        try:
            user_input = input("أنت: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user_input in ("خروج", "exit", "quit"):
            break
        if not user_input:
            continue
        checkpoint = len(messages)
        messages.append({"role": "user", "content": user_input})
        try:
            reply = chat_turn(client, messages)
        except anthropic.AuthenticationError:
            print("\n❌ مفتاح API غير صحيح. تأكد من ANTHROPIC_API_KEY.\n")
            del messages[checkpoint:]
            continue
        except anthropic.RateLimitError:
            print("\n⏳ وصلت للحد المسموح من الطلبات، انتظر شوي وجرّب مرة ثانية.\n")
            del messages[checkpoint:]
            continue
        except anthropic.APIConnectionError:
            print("\n🌐 مشكلة في الاتصال بالإنترنت، جرّب مرة ثانية.\n")
            del messages[checkpoint:]
            continue
        print(f"\nالمنسق: {reply}\n")


if __name__ == "__main__":
    main()
