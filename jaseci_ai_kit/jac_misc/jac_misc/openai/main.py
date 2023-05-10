"""
OpenAI Integration for Jaseci
Features:
    - GPT-3 (Completion and Chat)
    - Codex (Code Completion)
    - DALL-E (Image Generation)
    - Whispers (Audio Transcription)

Requires OpenAI API Key
"""

from jaseci.jsorc.live_actions import jaseci_action
from jaseci.utils.utils import logger
import os
import openai
from typing import Union


@jaseci_action(act_group=["openai"], allow_remote=True)
def setup(api_key=os.environ.get("OPENAI_API_KEY", None)):
    """
    Sets up OpenAI API Key

    :param api_key: str, required, default=None
                   OpenAI API key
    :return: bool
             Returns True if api_key is set, False otherwise
    """
    if not api_key:
        logger.error(
            "No OpenAI API Key Provided. Please set OPENAI_API_KEY environment variable or pass in api_key parameter though actions call openai.setup"
        )
        return False
    else:
        openai.api_key = api_key
        return True


@jaseci_action(act_group=["openai"], allow_remote=True)
def completion(
    prompt: Union[str, list] = "<|endoftext|>",
    model: str = "text-davinci-003",
    suffix: str = None,
    max_tokens: int = 16,
    temperature: float = 1,
    top_p: float = 1,
    n: int = 1,
    logprobs: int = None,
    echo: bool = False,
    stop: Union[str, list] = None,
    presence_penalty: float = 0,
    frequency_penalty: float = 0,
    best_of: int = 1,
):
    """
    Generate text completions based on a prompt using OpenAI's GPT-3 models.

    Parameters:
    ----------
    prompt : str or list of str, optional (default="")
        The prompt(s) to generate text completions for.
    model : str, optional (default="text-davinci-003")
        The name of the GPT-3 model to use for generating completions.
    suffix : str, optional (default=None)
        A suffix to append to the completion(s).
    max_tokens : int, optional (default=16)
        The maximum number of tokens to generate for each completion.
    temperature : float, optional (default=1.0)
        Controls the randomness of the generated completions. Higher values will result in more varied completions.
    top_p : float, optional (default=1.0)
        Controls the diversity of the generated completions. Lower values will result in more conservative completions.
    n : int, optional (default=1)
        The number of completions to generate.
    logprobs : int or None, optional (default=None)
        Controls whether to include log probabilities with the generated completions. If set to an integer value, the top n log probabilities for each token will be returned.
    echo : bool, optional (default=False)
        Controls whether the prompt should be included in the generated completions.
    stop : str, list of str, or None, optional (default=None)
        The sequence at which the model should stop generating text. If a list is provided, the model will stop at any of the specified sequences.
    presence_penalty : float, optional (default=0.0)
        Controls the model's tendency to generate new words or phrases. Higher values will result in more novel completions.
    frequency_penalty : float, optional (default=0.0)
        Controls the model's tendency to repeat words or phrases. Higher values will result in less repetitive completions.
    best_of : int, optional (default=1)
        Controls how many completions to return, and selects the best one(s) based on their log probabilities.

    Returns:
    -------
    completions : list of str
        A list of completions generated by the GPT-3 model based on the provided prompt(s).
    """

    response = openai.Completion.create(
        model=model,
        prompt=prompt,
        suffix=suffix,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        n=n,
        logprobs=logprobs,
        echo=echo,
        stop=stop,
        presence_penalty=presence_penalty,
        frequency_penalty=frequency_penalty,
        best_of=best_of,
    )
    response = [x.text for x in response.choices]
    return response


@jaseci_action(act_group=["openai"], allow_remote=True)
def chat(
    messages: list,
    model: str = "gpt-3.5-turbo",
    temperature: float = 1,
    top_p: float = 1,
    n: int = 1,
    stop: Union[str, list] = None,
    presence_penalty: float = 0,
    frequency_penalty: float = 0,
):
    """
    Generate responses to a list of messages using OpenAI's GPT-3.5 model.

    Parameters:
    ----------
    messages : list of str
        A list of messages to prompt the GPT-3.5 model with.
    model : str, optional (default='gpt-3.5-turbo')
        The name of the GPT-3.5 model to use for generating responses.
    temperature : float, optional (default=1.0)
        Controls the randomness of the generated responses. Higher values will result in more varied responses.
    top_p : float, optional (default=1.0)
        Controls the diversity of the generated responses. Lower values will result in more conservative responses.
    n : int, optional (default=1)
        The number of responses to generate for each message.
    stop : str, list of str, or None, optional (default=None)
        The sequence at which the model should stop generating text. If a list is provided, the model will stop at any of the specified sequences.
    presence_penalty : float, optional (default=0.0)
        Controls the model's tendency to generate new words or phrases. Higher values will result in more novel responses.
    frequency_penalty : float, optional (default=0.0)
        Controls the model's tendency to repeat words or phrases. Higher values will result in less repetitive responses.

    Returns:
    -------
    responses : list of str
        A list of responses generated by the GPT-3.5 model based on the provided messages.
    """

    response = openai.ChatCompletion.create(
        model=model,
        prompt=messages,
        temperature=temperature,
        top_p=top_p,
        n=n,
        stop=stop,
        presence_penalty=presence_penalty,
        frequency_penalty=frequency_penalty,
    )
    response = [x.message for x in response.choices]
    return response


@jaseci_action(act_group=["openai"], allow_remote=True)
def get_embeddings(input: Union[str, list], model: str = "text-embedding-ada-002"):
    """
    Returns the embedding of the input text(s) using the specified OpenAI embedding model.

    Parameters:
    -----------
    input: Union[str, list]
        The input text or a list of input texts to be embedded.
    model: str, optional (default="text-embedding-ada-002")
        The OpenAI embedding model to use.

    Returns:
    --------
    List[List[float]]:
        A list of embeddings, where each embedding is a list of floating-point numbers.
    """
    response = openai.Embedding.create(model=model, inputs=input)
    response = [x.embedding for x in response.data]
    return response


@jaseci_action(act_group=["openai"], allow_remote=True)
def transcribe(
    audio_file: str = None,
    audio_url: str = None,
    audio_array: list = None,
    model: str = "whisper-1",
    prompt: str = None,
    temperature: float = 0,
    language: str = None,
    translate=False,
):
    """
    Transcribes an audio file, audio URL, or audio array using the specified OpenAI Whisper model.

    Parameters:
    -----------
    audio_file: str, optional
        The path to the audio file to transcribe.
    audio_url: str, optional
        The URL of the audio file to transcribe.
    audio_array: list, optional
        A list containing the audio waveform as a sequence of floats between -1 and 1.
    model: str, optional (default="whisper-1")
        The OpenAI Whisper model to use for transcription.
    prompt: str, optional
        A prompt to use in addition to the audio input when transcribing with the OpenAI API.
    temperature: float, optional (default=0)
        The temperature to use when generating text for the transcription.
    language: str, optional
        The language of the audio being transcribed, specified as a BCP-47 language code.
    translate: bool, optional (default=False)
        If True, the transcribed text will be translated to English.

    Returns:
    --------
    str:
        The transcribed text.
    """
    if audio_array:
        import soundfile as sf
        import tempfile
        import numpy as np

        audio_array = np.array(audio_array)

        with tempfile.NamedTemporaryFile(suffix=".wav") as fp:
            sf.write(fp.name, audio_array, 16000)
            audio_file = fp.name
    if audio_url:
        import urllib.request
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".wav") as fp:
            urllib.request.urlretrieve(audio_url, fp.name)
            audio_file = fp.name

    audio_file = open(audio_file, "rb")
    if not translate:
        transcription = openai.Audio.transcribe(
            file=audio_file,
            model=model,
            prompt=prompt,
            temperature=temperature,
            language=language,
        )
    else:
        transcription = openai.Audio.translate(
            file=audio_file,
            model=model,
            prompt=prompt,
            temperature=temperature,
            language=language,
            translate=translate,
        )
    return transcription.text


@jaseci_action(act_group=["openai"], allow_remote=True)
def generate_image(
    prompt: str, n: int = 1, size: str = "512x512", response_format: str = "url"
):
    """
    Generate images using the DALL-E 2 API.

    Parameters:
    -----------
    prompt : str
        The textual prompt for generating the image(s).
    n : int, optional
        The number of images to generate (default is 1).
    size : str, optional
        The size of the image in pixels (default is "512x512").
    response_format : str, optional
        The format of the response, either "url" or "json" (default is "url").

    Returns:
    --------
    A list of generated images, either as URLs or Base64-encoded JSON strings,
    depending on the value of `response_format`.
    """
    response = openai.Image.create(
        prompt=prompt, n=n, size=size, response_format=response_format
    )
    response = [
        x.url if response_format == "url" else x.b64_json for x in response.data
    ]
    return response


@jaseci_action(act_group=["openai"], allow_remote=True)
def edit_image(
    prompt: str,
    image_file: str = None,
    mask_file: str = None,
    image_b64: str = None,
    mask_b64: str = None,
    n: int = 1,
    size: str = "512x512",
    response_format: str = "url",
):
    """
    DALL-E 2 Image Edit API.

    Args:
        prompt (str): Prompt describing the editing task.
        image_file (str, optional): Path to the input image file. Defaults to None.
        mask_file (str, optional): Path to the mask image file. Defaults to None.
        image_b64 (str, optional): Base64 encoded input image. Defaults to None.
        mask_b64 (str, optional): Base64 encoded mask image. Defaults to None.
        n (int, optional): Number of images to generate. Defaults to 1.
        size (str, optional): Size of the generated image. Defaults to "512x512".
        response_format (str, optional): Format of the response. "url" or "base64". Defaults to "url".

    Returns:
        List[str]: List of URLs or base64 encoded images.
    """
    if image_b64:
        import base64
        import tempfile

        image = base64.b64decode(image_b64)
        with tempfile.NamedTemporaryFile(suffix=".png") as fp:
            fp.write(image)
            image_file = fp.name
    if mask_b64:
        import base64
        import tempfile

        mask = base64.b64decode(mask_b64)
        with tempfile.NamedTemporaryFile(suffix=".png") as fp:
            fp.write(mask)
            mask_file = fp.name

    image = open(image_file, "rb")
    mask = open(mask_file, "rb")

    response = openai.Image.create_edit(
        prompt=prompt,
        n=n,
        size=size,
        response_format=response_format,
        image=image,
        mask=mask,
    )
    response = [
        x.url if response_format == "url" else x.b64_json for x in response.data
    ]
    return response


@jaseci_action(act_group=["openai"], allow_remote=True)
def variations_image(
    image_file: str = None,
    image_b64: str = None,
    n: int = 1,
    size: str = "512x512",
    response_format: str = "url",
):
    """
    Generates n variations of an image using the DALL-E 2 Image Variation API.

    :param image_file: (Optional) Path to the image file to use. If not provided, `image_b64` must be provided instead.
    :type image_file: str
    :param image_b64: (Optional) Base64-encoded image data. If not provided, `image_file` must be provided instead.
    :type image_b64: str
    :param n: (Optional) Number of variations to generate. Default is 1.
    :type n: int
    :param size: (Optional) Size of the output images in the format "<width>x<height>". Default is "512x512".
    :type size: str
    :param response_format: (Optional) Format of the response data. Can be "url" or "b64_json". Default is "url".
    :type response_format: str

    :return: A list of URLs or base64-encoded JSON strings representing the generated images.
    :rtype: List[str]
    """
    if image_b64:
        import base64
        import tempfile

        image = base64.b64decode(image_b64)
        with tempfile.NamedTemporaryFile(suffix=".png") as fp:
            fp.write(image)
            image_file = fp.name

    image = open(image_file, "rb")

    response = openai.Image.create_variation(
        n=n, size=size, response_format=response_format, image=image
    )
    response = [
        x.url if response_format == "url" else x.b64_json for x in response.data
    ]
    return response
