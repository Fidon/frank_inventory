$(function () {
  var CSRF_TOKEN = document
    .querySelector('meta[name="csrf-token"]')
    .getAttribute("content");

  function generate_errorsms(status, sms) {
    return `<div class="alert alert-${
      status ? "success" : "danger"
    } alert-dismissible fade show px-2 m-0 d-block w-100"><i class='fas fa-${status ? "check" : "exclamation"}-circle'></i> ${sms} <button type="button" class="btn-close d-inline-block" data-bs-dismiss="alert"></button></div>`;
  }

  $("#change_password_form").submit(function (e) {
    e.preventDefault();
    $.ajax({
      type: "POST",
      url: $(this).attr("action"),
      data: new FormData($(this)[0]),
      dataType: "json",
      contentType: false,
      processData: false,
      headers: {
        "X-CSRFToken": CSRF_TOKEN,
      },
      beforeSend: function () {
        $("#pass_cancel_btn").removeClass("d-inline-block").addClass("d-none");
        $("#pass_submit_btn")
          .html("<i class='fas fa-spinner fa-pulse'></i> Saving")
          .attr("type", "button");
      },
      success: function (response) {
        $("#pass_cancel_btn").removeClass("d-none").addClass("d-inline-block");
        $("#pass_submit_btn")
          .html("<i class='fas fa-check-circle'></i> Save")
          .attr("type", "submit");

        var fdback = generate_errorsms(response.success, response.sms);

        $("#change_password_form").animate({ scrollTop: 0 }, "slow");
        $("#change_password_form .formsms").html(fdback);

        if (response.success) {
          $("#change_password_form")[0].reset();
        }
      },
      error: function (xhr, status, error) {
        $("#pass_cancel_btn").removeClass("d-none").addClass("d-inline-block");
        $("#pass_submit_btn")
          .html("<i class='fas fa-check-circle'></i> Save")
          .attr("type", "submit");
        $("#change_password_form .formsms").html(
          generate_errorsms(false, "Unknown error, reload & try again")
        );
      },
    });
  });

  $("#profile_update_form").submit(function (e) {
    e.preventDefault();

    $.ajax({
      type: "POST",
      url: $(this).attr("action"),
      data: new FormData($(this)[0]),
      dataType: "json",
      contentType: false,
      processData: false,
      headers: {
        "X-CSRFToken": CSRF_TOKEN,
      },
      beforeSend: function () {
        $("#profile_cancel_btn")
          .removeClass("d-inline-block")
          .addClass("d-none");
        $("#profile_submit_btn")
          .html("<i class='fas fa-spinner fa-pulse'></i> Saving")
          .attr("type", "button");
      },
      success: function (response) {
        $("#profile_cancel_btn")
          .removeClass("d-none")
          .addClass("d-inline-block");
        $("#profile_submit_btn")
          .html("<i class='fas fa-check-circle'></i> Save")
          .attr("type", "submit");

        var fdback = generate_errorsms(response.success, response.sms);

        $("#profile_update_form").animate({ scrollTop: 0 }, "slow");
        $("#profile_update_form .formsms").html(fdback);

        if (response.success) {
          $("#user_div").load(location.href + " #user_div");
        }
      },
      error: function (xhr, status, error) {
        $("#profile_cancel_btn")
          .removeClass("d-none")
          .addClass("d-inline-block");
        $("#profile_submit_btn")
          .html("<i class='fas fa-check-circle'></i> Save")
          .attr("type", "submit");
        $("#profile_update_form .formsms").html(
          generate_errorsms(false, "Unknown error, reload & try again")
        );
      },
    });
  });
});
