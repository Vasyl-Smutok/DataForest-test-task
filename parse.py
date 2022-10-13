import asyncio
import csv
import json
import time
import httpx

from dataclasses import dataclass, astuple


PAGE_TO_PARSE = 200
from_numbers = [num for num in range(0, (PAGE_TO_PARSE + 1) * 20 - 20, 20)]


@dataclass
class Veterinarian:
    name: str
    address: str
    subtitle: str
    count_reviews: int
    avg_review_score: int


VETERINARIAN_FIELDS = list(Veterinarian.__dict__["__annotations__"].keys())


response = httpx.get(
    "https://www.zooplus.de/tierarzt/api/v2/token?debug=authReduxMiddleware-tokenIsExpired"
).content
token = json.loads(response)["token"]


async def get_all_info_about_veterinarians(
    num_page, from_number, client: httpx.AsyncClient
):
    result_json = {}

    response = await client.get(
        f"https://www.zooplus.de/tierarzt/api/v2/results?animal_99=true&page={num_page}&from={from_number}&size=20",
        headers={"authorization": f"Bearer {token}"},
    )

    result_json[num_page] = json.loads(response.content)

    return json.loads(response.content)


def get_detail_of_veterinarian(info: dict) -> Veterinarian:
    return Veterinarian(
        name=info["name"],
        address=info.get("address", ""),
        subtitle=info.get("subtitle", ""),
        count_reviews=int(info["count_reviews"]),
        avg_review_score=int(info["avg_review_score"]),
    )


async def parse() -> None:
    async with httpx.AsyncClient() as client:
        info_about_veterinarians = await asyncio.gather(
            *[
                get_all_info_about_veterinarians(
                    num_page, from_numbers[num_page], client
                )
                for num_page in range(1, PAGE_TO_PARSE)
            ]
        )

    all_veterinarians = []
    for num_page in range(0, PAGE_TO_PARSE):
        all_veterinarians.extend(
            [
                get_detail_of_veterinarian(veterinarian)
                for veterinarian in info_about_veterinarians[num_page - 1]["results"]
            ]
        )

    with open("data.csv", "w", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(VETERINARIAN_FIELDS)

        writer.writerows(astuple(veterinarian) for veterinarian in all_veterinarians)


if __name__ == "__main__":
    start_time = time.perf_counter()
    asyncio.run(parse())
    end_time = time.perf_counter()
    print("Elapsed:", round(end_time - start_time, 5))
