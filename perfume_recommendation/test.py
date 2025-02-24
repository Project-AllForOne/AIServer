import MeCab

# MeCab 태거 객체 생성
mecab = MeCab.Tagger()

# 예시 문장들
sentences = [
    "첫 향이 상쾌한 시트러스 계열이라 기분 좋게 시작돼. 시간이 지나면 부드러운 화이트 플로럴과 머스크가 어우러지면서 따뜻한 느낌을 주더라. 부담스럽지 않고 데일리로 사용하기 좋아!",
    "처음엔 스파이시한 우디 향이 강하게 느껴졌는데, 시간이 지나면서 바닐라와 앰버가 부드럽게 감싸주는 느낌이야. 남성적인 분위기가 강하면서도 고급스럽고 은은한 잔향이 오래 지속돼.",
    "맑고 깨끗한 아쿠아틱 계열의 향으로 시작해서 점점 시원한 그린 노트가 올라와. 여름철에 사용하면 청량감이 느껴지고, 잔향이 은은한 머스크와 섞여서 깔끔하게 마무리돼.",
    "처음엔 상큼한 프루티 노트가 튀는 느낌인데, 시간이 지나면서 따뜻한 우디와 파우더리한 향이 섞이면서 포근한 인상을 줘. 달콤하지만 너무 무겁지 않아서 부담 없이 사용하기 좋아.",
    "첫 향에서 오리엔탈 스파이시한 느낌이 강하게 퍼지다가, 중반부부터는 스모키한 타바코와 가죽 향이 더해지면서 묵직한 분위기를 만들어. 깊고 진한 향을 좋아하는 사람에게 추천하고 싶어.",
]

# 불용어 리스트 (예시)
stop_words = [
    "이",
    "가",
    "는",
    "을",
    "를",
    "에",
    "의",
    "와",
    "과",
    "으로",
    "에게",
    "다",
]

# 각 문장에 대해 형태소 분석 후 유의미한 단어 추출
for sentence in sentences:
    # 형태소 분석 결과
    result = mecab.parse(sentence)

    # 분석된 결과에서 'EOS' 제외하고 단어 리스트로 변환
    words = result.splitlines()[:-1]  # 마지막은 'EOS'이므로 제외

    # 유의미한 단어 추출 (명사, 형용사, 동사)
    meaningful_words = [
        word.split("\t")[0]
        for word in words
        if word.split("\t")[1].startswith(
            ("NNG", "XR", "VV", "VA")
        )  # 명사, 형용사, 동사
        and word.split("\t")[0] not in stop_words  # 불용어 제외
    ]

    # 출력
    print(f"Original Sentence: {sentence}")
    print(f"Meaningful Words: {meaningful_words}")
    print("-" * 50)
