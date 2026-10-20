const animatedBrands = document.querySelectorAll("[data-animated-brand]");
const titles = [
  { text: "Track Hub", language: "en" },
  { text: "追踪中心", language: "zh" },
  { text: "ट्रैक हब", language: "hi" },
  { text: "Centro de seguimiento", language: "es" },
  { text: "Centre de suivi", language: "fr" },
  { text: "مركز التتبع", language: "ar" },
  { text: "ট্র্যাকিং হাব", language: "bn" },
  { text: "Centro de rastreamento", language: "pt" },
  { text: "Центр отслеживания", language: "ru" },
  { text: "ٹریکنگ حب", language: "ur" },
  { text: "Pusat pelacakan", language: "id" },
  { text: "Tracking-Zentrale", language: "de" },
  { text: "追跡ハブ", language: "ja" },
  { text: "ਟ੍ਰੈਕਿੰਗ ਹੱਬ", language: "pa" },
  { text: "ट्रॅकिंग हब", language: "mr" },
  { text: "ట్రాకింగ్ హబ్", language: "te" },
  { text: "Takip merkezi", language: "tr" },
  { text: "கண்காணிப்பு மையம்", language: "ta" },
  { text: "Trung tâm theo dõi", language: "vi" },
  { text: "추적 허브", language: "ko" },
];

const typingDuration = 1000;
const readingDuration = 1400;
const deletingDuration = 600;

animatedBrands.forEach((brand) => {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    brand.textContent = titles[0].text;
    return;
  }

  const englishTitle = titles[0];
  const localizedTitles = titles.slice(1);
  let localizedIndex = 0;
  let titlesSinceEnglish = 2;

  const animateTitle = () => {
    const isEnglishTurn = titlesSinceEnglish === 2;
    const title = isEnglishTurn ? englishTitle : localizedTitles[localizedIndex];
    const characters = window.Intl?.Segmenter
      ? [...new Intl.Segmenter(title.language, { granularity: "grapheme" }).segment(title.text)].map(({ segment }) => segment)
      : Array.from(title.text);
    const typingDelay = typingDuration / characters.length;
    const deletingDelay = deletingDuration / characters.length;
    let characterIndex = 0;

    brand.textContent = "";
    brand.lang = title.language;
    brand.setAttribute("aria-label", title.text);

    const typeNextCharacter = () => {
      brand.textContent += characters[characterIndex];
      characterIndex += 1;

      if (characterIndex < characters.length) {
        window.setTimeout(typeNextCharacter, typingDelay);
      } else {
        window.setTimeout(deleteCharacter, readingDuration);
      }
    };

    const deleteCharacter = () => {
      characters.pop();
      brand.textContent = characters.join("");

      if (characters.length > 0) {
        window.setTimeout(deleteCharacter, deletingDelay);
      } else {
        if (isEnglishTurn) {
          titlesSinceEnglish = 0;
        } else {
          localizedIndex = (localizedIndex + 1) % localizedTitles.length;
          titlesSinceEnglish += 1;
        }

        window.setTimeout(animateTitle, 180);
      }
    };

    window.setTimeout(typeNextCharacter, typingDelay);
  };

  animateTitle();
});
