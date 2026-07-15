class ChartService:

    @staticmethod
    def suggest_chart(result):

        columns = result["columns"]

        if len(columns) != 2:
            return None

        x = columns[0]
        y = columns[1]

        return {
            "type": "bar",
            "x": x,
            "y": y
        }