$(function () {
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
  }

  const greetingsList = [
    "Niaje,",
    "Mambo vipi?",
    "Oooy,",
    "Harakati shazi,",
    "Unyama?",
    "Shwari?",
    "Harakati zinaenda?",
    "Pambania kombe,",
    "Upate pisi kwanza,",
    "Acha ungese,",
    "Maisha yana magepu,",
    "Sio poa,",
    "Si unyama lakini?",
    "Maisha jau,",
    "Cafe nao jau,",
    "We unaumwa nini?",
    "Uko poa?",
    "Kama kawa,",
    "Unaingia town?",
    "Wahuni jau,",
    "Niaje mzee,",
    "Back again?",
    "Tajiri kama Tajiri,",
    "Always a pleasure,",
    "Ila sio kiviile,",
    "Feeling good?",
    "Hope today’s treating you well,",
    "Vibes today?",
    "Still crushing it?",
    "Let’s win the day,",
    "Au we unaonaje,",
    "Here comes the champ,",
    "Bora umekuja,",
    "The legend returns,",
    "Hunaga baya,",
    "One of a kind!",
    "On fire today?",
    "Keep it up!",
    "Keep going strong!",
    "Motivated, eh?",
    "Shining bright today,",
    "Superstar!",
    "Baba lao,",
    "Happy to see you!",
    "Tupige kazi,",
    "Back to work?",
    "Si fresh lakini?",
    "Acha undanda,",
    "Ushatoka town,",
  ];

  // Time-based greeting (5 total)
  function getTimeBasedGreeting() {
    const hour = new Date().getHours();
    if (hour >= 5 && hour < 12) return "Good morning";
    if (hour >= 12 && hour < 17) return "Good afternoon";
    if (hour >= 17 && hour < 21) return "Good evening";
    return "Good night";
  }

  // Get random greeting
  function getRandomGreeting(username) {
    const timeGreeting = getTimeBasedGreeting();
    const allGreetings = [...greetingsList, timeGreeting];
    allGreetings.push(
      `Hope your ${timeGreeting.toLowerCase()} is going well`,
      `${timeGreeting}, ready to go?`,
      `${timeGreeting}, champ`,
      `Wishing you a lovely ${timeGreeting.toLowerCase()}`
    ); // total now = 50
    const randomIndex = Math.floor(Math.random() * allGreetings.length);
    return `${allGreetings[randomIndex]} ${username}`;
  }

  function timeDisplay() {
    const now = new Date();

    const dateOptions = {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    };

    const timeOptions = {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    };

    const formattedDate = now.toLocaleDateString(undefined, dateOptions);
    const formattedTime = now.toLocaleTimeString(undefined, timeOptions);

    $("#clock").html(`${formattedDate} ${formattedTime}`);
  }
  setInterval(timeDisplay, 1000);

  timeDisplay();
  var display_name_txt =
    getCookie("name_text") == null ? "Buda" : getCookie("name_text");
  $("#user_name_txt").text(getRandomGreeting(display_name_txt));
  $("#welcome-section").fadeIn("fast");
});
