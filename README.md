# AI-Commit 🤖✍️ 

## 📌 Introduction  

#### Generate smart, conventional Git commit messages with the power of AI.

##### AI-Commit is a command-line tool that analyzes your staged git changes and uses a Hugging Face model to generate a concise, well-formatted commit message for you. Stop worrying about wording and let the AI do the heavy lifting.

## 📖 Table of Contents  
- [Features](#-features)  
- [Installation](#-installation)  
- [Usage](#-usage)  
- [Configuration](#-configuration)  



## ✨ Features  
- 🔍 Automatic Message Generation: Analyzes your staged diff and creates a relevant commit message.
- 📋 Generates Commits Messages according to the [Conventional Commits specification](https://www.conventionalcommits.org/en/v1.0.0/) (`feat`, `fix`, `chore`, etc.).
- 🎨 Pretty-printed diffs and commit messages with [Rich](https://github.com/Textualize/rich).  
- 🔄 Interactive flow: accept, reject, edit, or regenerate messages.  
- 🔑 Works with Hugging Face models, optionally authenticated via `HF_TOKEN`.
- 🤖 Customizable Models: Use any compatible chat-based model from the [Hugging Face Hub](https://huggingface.co/docs/inference-endpoints/en/index).




## ⚙️ Installation  

### Prerequisites  
- Python **3.10+**  
- Git installed and available in your `PATH`  

### Install via source  
```bash
git clone https://github.com/JonathanYogev/ai-commit.git
cd ai-commit
pip install .
```

## 🚀 Usage


##### Stage your changes
```bash
git add <files>
```
##### Run AI Commit
```bash
ai-commit
```
### Options
`--model` <model> : Choose a Hugging Face model (default: meta-llama/Llama-3.2-3B-Instruct).
##### example:
```bash
ai-commit --model openai/gpt-oss-120b
```
## 🔧 Configuration

#### Hugging Face Token (optional):
Export your HF token if using a private or gated model:
```bash
export HF_TOKEN=your_token_here
```

