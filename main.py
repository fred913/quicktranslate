# coding: utf-8
from typing import Iterable, TypeAlias

import cachetools
import openai
import tiktoken
from fastapi import FastAPI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

app = FastAPI()

client = openai.AsyncOpenAI()

MAX_TOKENS: dict[str, int] = {
    "gpt-3.5-turbo": 3980,
    "gpt-3.5-turbo-16k": 15980
}


# @lru_cache(2048)
def build_prompt_to_tokenizer(
        prompt: Iterable[ChatCompletionMessageParam]) -> str:
    prompt_str = ""
    for p in prompt:
        content = p.get('content')
        if content is None:
            continue
        prompt_str += p['role'] + ": " + str(content) + "\n"
    return prompt_str


def count_tokens(query: str | Iterable[ChatCompletionMessageParam],
                 model: str = "gpt-3.5-turbo"):
    if not isinstance(query, str):
        query = build_prompt_to_tokenizer(query)
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(query))


async def request_llm_using_best_model(
        prompt: Iterable[ChatCompletionMessageParam],
        model_choices: list[str],
        temperature: float = 0.7,
        stop: str | None = None,
        max_prompt_gen_ratio: float = 0.4):
    model_choice = None
    for model in model_choices:
        # check token count
        token_count = count_tokens(prompt, model)
        max_tokens = MAX_TOKENS.get(model)
        if max_tokens is None:
            raise ValueError(f"Invalid model: {model}")
        if token_count > (max_tokens / (max_prompt_gen_ratio + 1) *
                          max_prompt_gen_ratio):
            # exceed max tokens, skip this model
            continue
        model_choice = model
        break
    if model_choice is None:
        raise ValueError("No valid model found for prompt; Prompt too long")

    completion = await client.chat.completions.create(
        messages=prompt,
        model=model_choice,
        temperature=temperature,
        max_tokens=MAX_TOKENS[model_choice],
        stop=stop,
        n=1,
    )
    return {
        "model": model_choice,
        "prompt": prompt,
        "completion": completion.choices[0].message.content,
    }


@app.get("/")
async def root():
    return {"message": "service working", "status": True}


LanguageModeType: TypeAlias = str
AutoLangType: TypeAlias = Iterable[LanguageModeType]

# TODO: algo-based auto language detection
AUTOLANG_ZH_EN: AutoLangType = "auto:zh-en", "auto:en-zh"


def is_valid_lang(lang: str):
    valid_languages = {
        "en", "en_US", "en_GB", "zh", "zh_CN", "zh_TW", "ja", *AUTOLANG_ZH_EN
    }
    return lang.lower() in {i.lower() for i in valid_languages}


# 65536 cache entries with a TTL of 1 day
cache_mod = cachetools.TTLCache(maxsize=65536, ttl=60 * 60 * 24)


@app.get("/translate")
async def translate(text: str, to_lang: str):
    if not is_valid_lang(to_lang):
        return {
            "message": f"Invalid language code: {to_lang}",
            "status": False
        }

    # check cache
    cache_key = f"To_{to_lang}:{text}"
    if cache_key in cache_mod:
        return cache_mod[cache_key]

    gpt_llm_prompt = ""
    if to_lang in AUTOLANG_ZH_EN:
        gpt_llm_prompt += f"Please translate the text to Chinese(if its now english) or English(if its now Chinese) keeping all formats and some special characters intact:\n"
        to_lang = "that kind of language"
    else:
        gpt_llm_prompt += f"Please translate the text to \"{to_lang}\" keeping all formats and some special characters intact:\n"
    gpt_llm_prompt += "```\n"
    gpt_llm_prompt += text.replace("```", "\\`\\`\\`")
    gpt_llm_prompt += "\n```"

    response = await request_llm_using_best_model(prompt=[{
        "role":
        "system",
        "content":
        "You're an AI language model that helps the user translate text to any existing language."
    }, {
        "role":
        "user",
        "content":
        gpt_llm_prompt
    }, {
        "role":
        "assistant",
        "content":
        f"Sure. I'm famaliar with {to_lang}. Here's my translation:\n```\n"
    }],
                                                  model_choices=[
                                                      "gpt-3.5-turbo",
                                                      "gpt-3.5-turbo-16k"
                                                  ],
                                                  temperature=0.35,
                                                  stop="\n```")
    response["translation"] = response.pop("completion").replace(
        "\\`\\`\\`", "```")
    response.pop("prompt")
    response.update({"status": True, "message": ""})

    # cache
    cache_mod[cache_key] = response

    return response


class TranslationRequest(BaseModel):
    text: str
    to_lang: str


@app.post("/translate")
async def translate_post(data: TranslationRequest):
    text = data.text
    to_lang = data.to_lang
    return await translate(text, to_lang)


if __name__ == "__main__":
    # print("Number of tokens:", count_tokens(input("Enter text to encode: ")))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
