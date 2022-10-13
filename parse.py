import asyncio
import csv
import json
import time
import httpx

from dataclasses import dataclass, astuple


PAGE_TO_PARSE = 15


@dataclass
class Veterinarian:
    name: str
    address: str
    subtitle: str
    count_reviews: int
    avg_review_score: int


VETERINARIAN_FIELDS = list(Veterinarian.__dict__["__annotations__"].keys())


response = httpx.get("https://www.zooplus.de/tierarzt/api/v2/token?debug=authReduxMiddleware-tokenIsExpired").content
token = json.loads(response)["token"]


async def get_all_info_about_veterinarians(client: httpx.AsyncClient) -> dict:
    result_json = {}
    from_number = 0

    for num_page in range(1, PAGE_TO_PARSE + 1):
        response = await client.get(
            f"https://www.zooplus.de/tierarzt/api/v2/results?animal_99=true&page={num_page}&from={from_number}&size=20",
            headers={"authorization": f"Bearer {token}"}
        )

        result_json[num_page] = json.loads(response.content)
        from_number += 20

    return result_json


def get_detail_of_veterinarian(info: dict) -> Veterinarian:
    try:
        subtitle = info["subtitle"]
    except KeyError:
        subtitle = ""

    return Veterinarian(
        name=info["name"],
        address=info["address"],
        subtitle=subtitle,
        count_reviews=int(info["count_reviews"]),
        avg_review_score=int(info["avg_review_score"]),
    )


async def parse() -> None:
    async with httpx.AsyncClient() as client:
        info_about_veterinarians = await get_all_info_about_veterinarians(client)

    all_veterinarians = []
    for page_num in range(1, PAGE_TO_PARSE + 1):
        all_veterinarians.extend(
            [
                get_detail_of_veterinarian(veterinarian)
                for veterinarian in (info_about_veterinarians[page_num]["results"])
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
    print(end_time - start_time)
