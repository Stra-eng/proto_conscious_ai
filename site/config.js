// Вставьте реальные ссылки перед запуском. Пока там "#", кнопки ведут на форму заявки.
window.SITE_CONFIG = {
  brand: "AI Globe",
  // Stripe Payment Links (Dashboard → Payment Links). Один и тот же линк принимает
  // карты, Apple Pay, Google Pay, SEPA, iDEAL, Klarna и др. — включается в настройках Stripe.
  payLinks: { start: "#", team: "#", crypto: "#" },
  // Куда уходят B2B-заявки (Formspree/Getform/свой endpoint). Пусто = откроется почтовый клиент.
  b2bEndpoint: "",
  contactEmail: "hello@example.com"
};
