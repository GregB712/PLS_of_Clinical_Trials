# Master's Thesis: Plain Language Summarization of Clinical Trials

📘 **Thesis Title:** Plain Language Summarization of Clinical Trials  
🎓 **Institution:** Aristotle University of Thessaloniki  
📅 **Submission Date:** September, 2024
📄 **Published Version:** [ikee.lib.auth.gr link](http://ikee.lib.auth.gr/record/359574)

---

## 🧠 Overview

This repository contains the code and documentation related to my Master's Thesis submitted to the [School of Informatics](https://www.csd.auth.gr/en/) at the Aristotle University of Thessaloniki, as part of the MSc in Data and Web Science program.

The work focuses on:

> This thesis explores the challenge of making clinical trial findings accessible to the general public by translating them into plain language. It introduces a custom dataset of 286 clinical trials and their simplified summaries, and evaluates the performance of two NLP models—fine-tuned DistilBERT and Mistral-7B-Instruct—in generating readable, accurate translations. The work highlights both the potential and limitations of large language models in improving health communication.


For full details, please refer to the [ikee.lib.auth.gr link](http://ikee.lib.auth.gr/record/359574) hosted by the university library.

---

## 📂 Repository Structure

├── Extra Code/ # Additional scripts used for automation and testing 

├── Preprocess Dataset/ # Code for preprocessing the clinical trial dataset 

├── model.ipynb # Jupyter notebook for model training and evaluation

└── README.md # Project overview and documentation. You’re here!


---

## 🚀 Technologies Used

This thesis leverages modern machine learning and natural language processing (NLP) tools to build and evaluate models for plain language summarization of clinical trial documents. Key technologies and tools include:

- **Python 3.10** – Primary programming language for all experimentation and scripting.
- **Hugging Face Transformers** – Used for model loading, fine-tuning, and inference, especially with:
  - `DistilBERT`: a lightweight version of BERT fine-tuned on the custom clinical trial dataset.
- **LangChain** – For orchestrating interactions with large language models and managing prompt templates.
- **Mistral-7B-Instruct** – A powerful open-source large language model tested without fine-tuning for zero-shot summarization.
- **PyTorch** – Backend framework for training and fine-tuning transformer models.
- **Datasets Library (Hugging Face)** – Used to manage and manipulate text datasets efficiently.
- **scikit-learn & pandas** – For data preprocessing and analysis.
- **Matplotlib & Seaborn** – For generating visualizations of results and evaluation metrics.
- **Evaluation Metrics**:
  - **ROUGE**, **BLEU**, and **F1 Score** – Used to assess the performance of generated summaries.

Additional techniques applied include:
- **Gradient Checkpointing** and **Mixed Precision Training** – To optimize memory and computation during training.
- **Custom Prompt Engineering** – Designed to tailor responses from the Mistral model to clinical summarization tasks.

---

## 📝 Citation

If you find this work useful, please consider citing:

@mastersthesis{Barmpas2025thesis, title = {Plain Language Summarization of Clinical Trials}, author = {Grigorios Barmpas}, school = {Aristotle University of Thessaloniki}, year = {2024}, url = {https://ikee.lib.auth.gr/record/359574} }

## 📬 Contact

For questions, collaborations, or discussions:

- GitHub: [GregB712](https://github.com/GregB712)
- Email: [gregorybarbas@gmail.com]

---

## 📌 Notes

> This repository is maintained as a public reference for academic and personal portfolio purposes.
