import g4f


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
    )
    for message in response:
        print(message, flush=True, end='')


def gpt2(content):
    response = g4f.ChatCompletion.create(
        model="gpt-3.5-turbo",
        provider=g4f.Provider.Feedough,
        messages=[{"role": "user", "content": content}],
        stream=True,
    )
    for message in response:
        print(message)


def gpt3(content):
    response = g4f.ChatCompletion.create(
        model="gpt-3.5-turbo",
        provider=g4f.Provider.FlowGpt,
        messages=[{"role": "user", "content": content}],
        stream=True,
    )
    for message in response:
        print(message)


if __name__ == '__main__':
    gpt1("Ты умеешь решать уравнения?")
