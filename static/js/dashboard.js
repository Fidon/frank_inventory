$(function () {
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
});
