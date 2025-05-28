import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import pandas as pd
import matplotlib.pyplot as plt
import subprocess
import re

class CSVChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV q&a with a llama")

        self.df = None

        #user interface setup
        self.load_button = tk.Button(root,text= "Load CSV", command=self.load_csv)
        self.load_button.pack(pady=5)

        self.question_entry = tk.Entry(root, width=80)
        self.question_entry.pack(pady=5)
        self.question_entry.bind("<Return>", self.ask_question)

        self.ask_button = tk.Button(root, text="Ask", command=self.ask_question)
        self.ask_button.pack(pady=5)

        self.answer_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=100, height=20)
        self.answer_box.pack(pady=5)

    def load_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not path:
            return
        try:
            self.df = pd.read_csv(path)
            messagebox.showinfo("CSV Loaded", f"loaded {len(self.df)} rows.")
        except Exception as e:
            messagebox.showerror("ERROR", str(e))
    

    def ask_question(self, event=None):
        if self.df is None:
            messagebox.showwarning("No CSV", "Please load a CSV file first.")
            return

        query = self.question_entry.get().strip()
        if not query:
            return

    
        self.answer_box.insert(tk.END, f"\nQuestion: {query}\n")
        self.answer_box.see(tk.END)

        try:
            prompt = (
                f"You are a helpful data analyst working with a pandas DataFrame named `df`.\n\n"
                f"The columns in the DataFrame are: {', '.join(self.df.columns)}.\n\n"
                f"Answer the following question using plain English. Do not return any Python code unless the user explicitly asks for code or a chart.\n"
                f"Just give the answer without explaining how to get the answer.\n"
                f"Only include matplotlib code if the user specifically asks for a chart or visualization.\n"
                f"If you do generate a chart, return only the code wrapped in triple backticks.\n\n"
                f"Question: \"{query}\""
            )

            result = subprocess.run(
                ["ollama", "run", "granite3.3:2b"],
                input=prompt,
                text=True,
                capture_output=True,
                check=True,
                encoding='utf-8'
            )

            output = result.stdout.strip()
            self.answer_box.insert(tk.END, f"Raw output:\n{output}\n\n")

            code_match = re.search(r"```(?:python)?(.*?)```", output, re.DOTALL)
            if code_match:
                if any(word in query.lower() for word in ["chart", "plot", "graph", "visual"]):
                    code = code_match.group(1).strip()
                    self.answer_box.insert(tk.END, f"Generated code:\n{code}\n\n")
                    self.answer_box.insert(tk.END, "Plotting chart...\n")
                    self.answer_box.insert(tk.END, f"Available columns: {list(self.df.columns)}\n\n")
                    self.safe_exec(code)
                else:
                    self.answer_box.insert(tk.END, "Code was returned but user did not ask for a chart.\n")
                    self.answer_box.insert(tk.END, f"{output}\n\n")
            elif "plt." in output:
            # If LLM returned unformatted code
                self.answer_box.insert(tk.END, "Detected raw matplotlib code — trying to run...\n")
                self.safe_exec(output)
            else:
            # Just regular answer
                self.answer_box.insert(tk.END, f"{output}\n\n")

        except subprocess.CalledProcessError as e:
            self.answer_box.insert(tk.END, f"Subprocess error: {e.stderr.strip()}\n\n")
        except Exception as e:
            self.answer_box.insert(tk.END, f"Exception: {str(e)}\n\n")

        self.answer_box.see(tk.END)
        self.question_entry.delete(0, tk.END)

    def safe_exec(self, code):
        try:
            exec(code, {"df": self.df, "plt": plt, "pd": pd})
            plt.show()
        except Exception as e:
            self.answer_box.insert(tk.END, f"Chart error: {str(e)}\n\n")
            self.answer_box.insert(tk.END, f"Available columns: {list(self.df.columns)}\n\n")
            messagebox.showerror("Chart Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = CSVChatApp(root)
    root.mainloop()
