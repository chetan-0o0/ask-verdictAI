import os
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
print("step 1: imports")
import gradio as gr
print("step 2: building UI")
with gr.Blocks() as demo:
    gr.HTML("<h1>Test</h1>")
    btn = gr.Button("Click")
print("step 3: launching")
demo.launch(server_name="127.0.0.1", server_port=7860)
print("step 4: launched")
