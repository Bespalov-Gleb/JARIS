import g4f
from g4f.client import Client


# ['AItianhuSpace', 'Aichatos', 'Aura', 'Bing', 'BingCreateImages', 'Blackbox', 'ChatForAi', 'Chatgpt4Online',
# 'ChatgptAi', 'ChatgptNext', 'ChatgptX', 'Cnote', 'Cohere', 'DeepInfra', 'DeepInfraImage', 'DuckDuckGo', 'Ecosia',
# 'Feedough', 'FlowGpt', 'FreeChatgpt', 'FreeGpt', 'Gemini', 'GeminiPro', 'GeminiProChat', 'GigaChat', 'GptTalkRu',
# 'Groq', 'HuggingChat', 'HuggingFace', 'Koala', 'Liaobots', 'Llama', 'Local', 'MetaAI', 'MetaAIAccount', 'MyShell',
# 'OpenRouter', 'Openai', 'OpenaiAccount', 'OpenaiChat', 'PerplexityAi', 'PerplexityLabs', 'Pi', 'Poe', 'Raycast',
# 'Replicate', 'ReplicateImage', 'TalkAi', 'Theb', 'ThebApi', 'Vercel', 'WhiteRabbitNeo', 'You', 'Yqcloud']

def gpt1(content):
    response = g4f.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": content}],
        stream=True,
        provider=g4f.Provider.Aichatos
    )

    return response


def gpt2(content):
    response = g4f.ChatCompletion.create(
        model="gpt-3.5-turbo",
        provider=g4f.Provider.Feedough,
        messages=[{"role": "user", "content": content}],
        stream=True,
    )

    return response


def gpt3(content):
    response = g4f.ChatCompletion.create(
        model="gpt-3.5-turbo",
        provider=g4f.Provider.FlowGpt,
        messages=[{"role": "user", "content": content}],
        stream=True,
    )

    return response


if __name__ == '__main__':
    gpt_func = gpt1

    for message in gpt_func("Сколько будет 13 умножить на 16"):
        print(str(message))
