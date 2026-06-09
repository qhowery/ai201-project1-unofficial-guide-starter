import gradio as gr
from generator import ask


def handle_query(question: str):
    res = ask(question)
    answer = res.get("answer", "")
    sources = res.get("sources", [])
    sources_text = "\n".join(f"• {s}" for s in sources)
    return answer, sources_text


def main():
    with gr.Blocks() as demo:
        gr.Markdown("# Professor Reviews — Q&A")
        inp = gr.Textbox(label="Your question")
        btn = gr.Button("Ask")
        answer = gr.Textbox(label="Answer", lines=8)
        sources = gr.Textbox(label="Retrieved from", lines=4)
        btn.click(handle_query, inputs=inp, outputs=[answer, sources])
        inp.submit(handle_query, inputs=inp, outputs=[answer, sources])

    demo.launch()

if __name__ == "__main__":
    main()
