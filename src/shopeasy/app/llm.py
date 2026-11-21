from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()


def get_model():
    llm = ChatGroq(
        model= "openai/gpt-oss-120b"
    )
    return llm


if __name__ == "__main__":
    llm = get_model()
    print(llm.invoke("hi my name is bhavesh"))