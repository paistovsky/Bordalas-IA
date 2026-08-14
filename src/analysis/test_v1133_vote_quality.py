
def score(
    tier,
    coverage,
    probability,
    starter_votes,
    bench_votes,
    base,
):
    vote_quality = (
        starter_votes
        * 5000.0
        -
        bench_votes
        * 5000.0
    )

    return (
        tier
        * 100000.0
        +
        vote_quality
        +
        coverage
        * 3000.0
        +
        probability
        * 100.0
        +
        base
    )


def main():
    javi_like = score(
        3, 3, 50, 1, 0, 10
    )

    jonny_like = score(
        3, 3, 50, 1, 1, 10
    )

    etta_like = score(
        3, 3, 50, 0, 1, 1000
    )

    assert (
        javi_like
        >
        jonny_like
        >
        etta_like
    )

    confirmed = score(
        5, 2, 70, 2, 0, 0
    )

    uncertain = score(
        3, 3, 59, 1, 0, 9999
    )

    assert confirmed > uncertain

    print(
        "V11.3.3 VOTE QUALITY: 2/2 OK"
    )


if __name__ == "__main__":
    main()
