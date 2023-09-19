import pathlib
from platform import system

from fastai.collab import load_learner


def read_learner(path_pkl):
    if system() == "Linux":
        pathlib.WindowsPath = (
            pathlib.PosixPath
        )  # if model is trained and stored on a Windows machine but deployed on Linux
    learn = load_learner(path_pkl)

    return learn
