import time


def log_error(error: Exception) -> None:
    print("[ERROR]", error)
    with open("log.txt", "a") as log:
        log.write(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()) + " | [ERROR] | " + str(error) + "\n")
        log.close()


def log_warning(text: str) -> None:
    print("[WARN]", text)
    with open("log.txt", "a") as log:
        log.write(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()) + " | [WARN] | " + text + "\n")
        log.close()


def log_message(text: str) -> None:
    print("[MSG]", text)
    with open("log.txt", "a") as log:
        log.write(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()) + " | [MSG] | " + text + "\n")
        log.close()
