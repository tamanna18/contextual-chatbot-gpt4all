import argparse
import os
import sys
from pathlib import Path

from conversation.question_answer import (QuestionAndAnswer,
                                          QuestionAndAnswerConfig)
from helpers.extractor import extract_answer
from helpers.model import load_gpt4all
from helpers.log import get_logger
from memory.vector_memory import VectorMemory, initialize_embedding
from conversation.prompts import CONDENSE_QUESTION_PROMPT, QA_PROMPT
from rich.console import Console
from rich.markdown import Markdown

logger = get_logger(__name__)


def run_chatbot_loop(qa: QuestionAndAnswer) -> None:
    console = Console(color_system="windows")
    console.print(
        "[bold magenta]Hi! 👋, I'm your friendly chatbot 🦜 here to assist you. How can I help you today? [/bold "
        "magenta]Type 'exit' to stop."
    )
    chat_history = []
    while True:
        console.print("[bold green]Please enter your question:[/bold green]")
        question = input("")

        if question.lower() == "exit":
            break
        logger.info(f"question: {question}, chat_history: {chat_history}")

        # Generate the answer using the ConversationalRetrievalChain
        result = qa.generate_answer(question, chat_history)
        console.print("\n[bold magenta]Full answer:[/bold magenta]")
        console.print(Markdown(result["answer"]))

        answer = extract_answer(result["answer"])

        # Collect the history
        chat_history.append((question, answer))

        console.print(f"\n[bold green]Question:[/bold green]{question}")
        console.print("\n[bold green]Answer:[/bold green]")
        if answer:
            console.print(Markdown(answer))
        else:
            console.print("[bold red]Something went wrong![/bold red]")


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI Chatbot")
    parser.add_argument(
        "--k",
        type=int,
        help="Number of chunks to return from the similarity search. Defaults to 2.",
        required=False,
        default=2,
    )

    return parser.parse_args()


def main(parameters):
    root_folder = Path(__file__).resolve().parent.parent
    model_path = root_folder / "models" / "ggml-model-q4_0.bin"
    vector_store_path = root_folder / "vector_store" / "docs_index"

    n_threads = int(os.cpu_count() - 1)

    llm = load_gpt4all(str(model_path), n_threads)
    embedding = initialize_embedding()

    memory = VectorMemory(embedding=embedding)
    index = memory.load_memory_index(str(vector_store_path))

    qa_config = QuestionAndAnswerConfig(
        llm, index, CONDENSE_QUESTION_PROMPT, QA_PROMPT, k=parameters.k
    )
    qa = QuestionAndAnswer(qa_config)

    run_chatbot_loop(qa)


if __name__ == "__main__":
    try:
        args = get_args()
        main(args)
    except Exception as error:
        logger.error(f"An error occurred: {str(error)}", exc_info=True, stack_info=True)
        sys.exit(1)