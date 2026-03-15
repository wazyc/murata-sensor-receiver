class MurataExceptionBase(Exception):
    """村田センサー関連の例外の基底クラス"""

    def __init__(self, message: str = "", details: str = ""):
        """
        Args:
            message: エラーメッセージ
            details: エラーの詳細情報
        """
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - {self.details}"
        return self.message


class FailedCheckSum(MurataExceptionBase):
    """電文全体のチェックサムエラー"""

    def __init__(self, details: str = ""):
        super().__init__("Failed to validate message checksum", details)


class FailedCheckSumPayload(MurataExceptionBase):
    """ペイロードのチェックサムエラー"""

    def __init__(self, details: str = ""):
        super().__init__("Failed to validate payload checksum", details)
