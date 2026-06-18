from src.parser.duviriRotation import getDuvWarframe, getDuvIncarnon


def checkCircuitWarframe(obj_new):
    return getDuvWarframe()["Choices"] != obj_new[0]["CategoryChoices"][0]["Choices"]


def checkCircuitIncarnon(obj_new):
    return getDuvIncarnon()["Choices"] != obj_new[0]["CategoryChoices"][1]["Choices"]
