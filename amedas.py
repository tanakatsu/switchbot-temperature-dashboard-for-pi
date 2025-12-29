import time
from datetime import date, datetime, timedelta

import pandas as pd
import requests


class AmedasDataClient:
    def __init__(self, location_id: str, interval_minute: int = 10):
        """初期化

        Args:
            location_id (str): 観測地点のID
            interval_minute (int, optional): 取得間隔（分）

        Raises:
            ValueError: 取得間隔が10, 20, 30, 60でないとき
        """
        self.location_id = location_id
        self.interval_minute = interval_minute

        if self.interval_minute not in (10, 20, 30, 60):
            raise ValueError("取得間隔は10, 20, 30, 60のいずれかを指定してください")

    def fetch(self, start_date: date, end_date: date) -> pd.DataFrame:
        """期間を指定してサーバーからデータ取得

        Args:
            start_date (date): 開始日
            end_date (date): 終了日

        Returns:
            pd.DataFrame: 取得したデータ

        Raises:
            ValueError: 開始日と終了日の時間関係が間違っているとき
            ValueError: 取得期間が10日以内でないとき
        """

        if start_date > end_date:
            raise ValueError("開始日と終了日を入れ替えてください")

        if date.today() + timedelta(days=-10) > start_date:
            raise ValueError("取得期間は10日以内で指定してください")

        df_list = []
        current_date = start_date
        while current_date <= end_date:
            for hour in range(24):
                for minute in range(0, 60, self.interval_minute):
                    dt = datetime(
                        current_date.year,
                        current_date.month,
                        current_date.day,
                        hour,
                        minute,
                        0,
                    )
                    df = self.fetch_one(dt)
                    df_list.append(df)
                    time.sleep(0.1)

            current_date += timedelta(days=1)

        final_df = pd.concat(df_list)
        final_df = final_df.set_index("time")
        return final_df

    def fetch_one(self, dt: datetime) -> pd.DataFrame:
        """
        指定した日時のデータを1件取得する

        Args:
            dt (datetime): 取得対象日時

        Returns:
            pd.DataFrame: 取得したデータ

        Raises:
            ValueError: 取得時刻が10分単位でないとき
            ValueError: 観測地点IDが存在しないとき
            ValueError: 指定した日時のデータが存在しないとき
        """
        base_url = "https://www.jma.go.jp/bosai/amedas/data/map/"
        url = f"{base_url}{dt.strftime('%Y%m%d%H%M%S')}.json"

        if not (dt.minute % 10 == 0 and dt.second == 0 and dt.microsecond == 0):
            raise ValueError("取得時刻は10分単位で指定してください")

        response = requests.get(url)
        if response.status_code == 404:
            raise ValueError("指定した日時のデータは存在しません")

        data = response.json()
        df = pd.DataFrame(data).T

        if self.location_id not in df.index:
            raise ValueError(f"指定した観測地点ID({self.location_id})は存在しません")

        one_data = {}
        one_data["time"] = dt

        for k, v in df.loc[self.location_id].items():
            if isinstance(v, list):
                one_data[k] = v[0]
            else:
                one_data[k] = v

        return pd.DataFrame([one_data])

    def get_observation_points(self) -> pd.DataFrame:
        """観測地点一覧を取得する

        Returns:
            pd.DataFrame: 観測地点一覧
        """
        url = "https://www.jma.go.jp/bosai/amedas/const/amedastable.json"

        response = requests.get(url)
        data = response.json()

        df_observation_points = pd.DataFrame(data).T
        return df_observation_points
