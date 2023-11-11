class DataPrintable:
    def __str__(self):
        return f"<{self.__class__.__name__}\n" \
               f"    {str(self.__dict__)}\n" \
               f">"
