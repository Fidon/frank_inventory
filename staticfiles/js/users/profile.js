class ProfileManager {
  constructor() {
    this.config = {
      csrfToken: this.getCSRFToken(),
    };

    this.selectors = {
      passwordForm: "#change_password_form",
      profileForm: "#profile_update_form",
      passwordCancelBtn: "#pass_cancel_btn",
      passwordSubmitBtn: "#pass_submit_btn",
      profileCancelBtn: "#profile_cancel_btn",
      profileSubmitBtn: "#profile_submit_btn",
      userDiv: "#user_div",
    };

    this.init();
  }

  /**
   * Get CSRF token from meta tag
   */
  getCSRFToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    return metaTag ? metaTag.getAttribute("content") : "";
  }

  /**
   * Initialize the application
   */
  init() {
    this.setupFormHandlers();
  }

  /**
   * Generate alert messages
   */
  generateAlert(isSuccess, message) {
    const alertType = isSuccess ? "success" : "danger";
    const iconType = isSuccess ? "check" : "exclamation";

    return `
      <div class="alert alert-${alertType} alert-dismissible fade show px-2 m-0 d-block w-100">
        <i class='fas fa-${iconType}-circle'></i> ${message}
        <button type="button" class="btn-close d-inline-block" data-bs-dismiss="alert"></button>
      </div>
    `;
  }

  /**
   * Setup form submission handlers
   */
  setupFormHandlers() {
    $(this.selectors.passwordForm).on("submit", (e) =>
      this.handlePasswordFormSubmit(e)
    );
    $(this.selectors.profileForm).on("submit", (e) =>
      this.handleProfileFormSubmit(e)
    );
  }

  /**
   * Set form loading state
   */
  setFormLoading(isLoading, cancelBtnSelector, submitBtnSelector) {
    const cancelBtn = $(cancelBtnSelector);
    const submitBtn = $(submitBtnSelector);

    if (isLoading) {
      cancelBtn.removeClass("d-inline-block").addClass("d-none");
      submitBtn
        .html("<i class='fas fa-spinner fa-pulse'></i> Saving")
        .attr("type", "button");
    } else {
      cancelBtn.removeClass("d-none").addClass("d-inline-block");
      submitBtn
        .html("<i class='fas fa-check-circle'></i> Save")
        .attr("type", "submit");
    }
  }

  /**
   * Scroll to top utility
   */
  scrollToTop(selector) {
    $(selector).animate({ scrollTop: 0 }, "slow");
  }

  /**
   * Handle AJAX form submission
   */
  handleAjaxSubmit(
    formSelector,
    cancelBtnSelector,
    submitBtnSelector,
    successCallback
  ) {
    const form = $(formSelector);

    $.ajax({
      type: "POST",
      url: form.attr("action"),
      data: new FormData(form[0]),
      dataType: "json",
      contentType: false,
      processData: false,
      headers: { "X-CSRFToken": this.config.csrfToken },
      beforeSend: () =>
        this.setFormLoading(true, cancelBtnSelector, submitBtnSelector),
      success: (response) => {
        this.setFormLoading(false, cancelBtnSelector, submitBtnSelector);
        const feedback = this.generateAlert(response.success, response.sms);
        this.scrollToTop(formSelector);
        $(`${formSelector} .formsms`).html(feedback);
        successCallback(response);
      },
      error: () => {
        this.setFormLoading(false, cancelBtnSelector, submitBtnSelector);
        const feedback = this.generateAlert(
          false,
          "Unknown error, reload & try again"
        );
        this.scrollToTop(formSelector);
        $(`${formSelector} .formsms`).html(feedback);
      },
    });
  }

  /**
   * Handle password form submission
   */
  handlePasswordFormSubmit(e) {
    e.preventDefault();
    this.handleAjaxSubmit(
      this.selectors.passwordForm,
      this.selectors.passwordCancelBtn,
      this.selectors.passwordSubmitBtn,
      (response) => {
        if (response.success) {
          $(this.selectors.passwordForm)[0].reset();
        }
      }
    );
  }

  /**
   * Handle profile form submission
   */
  handleProfileFormSubmit(e) {
    e.preventDefault();
    this.handleAjaxSubmit(
      this.selectors.profileForm,
      this.selectors.profileCancelBtn,
      this.selectors.profileSubmitBtn,
      (response) => {
        if (response.success) {
          $(this.selectors.userDiv).load(
            `${location.href} ${this.selectors.userDiv}`
          );
        }
      }
    );
  }
}

// Initialize the application when DOM is ready
$(function () {
  new ProfileManager();
});
