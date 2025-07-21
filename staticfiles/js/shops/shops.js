class ShopsManager {
  constructor() {
    this.config = {
      columnIndices: [0, 1, 2, 3, 4, 5, 6],
      dateCache: { start: null, end: null },
      csrfToken: this.getCSRFToken(),
      deletingState: false,
    };

    this.selectors = {
      form: "#new_shop_form",
      table: "#shops_table",
      canvas: "#new_shop_canvas",
      cancelBtn: "#shop_cancel_btn",
      submitBtn: "#shop_submit_btn",
      searchInput: "#shops_search",
      clearFilter: "#shops_filter_clear",
      minDate: "#min_date",
      maxDate: "#max_date",
      dateClear: "#date_clear",
      dateFilterBtn: "#date_filter_btn",
      confirmDeleteBtn: "#confirm_delete_btn",
      cancelDeleteBtn: "#cancel_delete_btn",
      shopsDiv: "#shop_div",
      shopsListUrl: "#shops_list_url",
      shopId: "#get_shop_id",
      deleteModal: "#confirm_delete_modal",
    };

    this.table = null;
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
    this.setupFormHandler();
    this.setupTable();
    this.setupEventHandlers();
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
   * Setup form submission handler
   */
  setupFormHandler() {
    $(this.selectors.form).on("submit", (e) => this.handleFormSubmit(e));
  }

  /**
   * Handle form submission
   */
  handleFormSubmit(e) {
    e.preventDefault();
    const form = $(this.selectors.form);

    $.ajax({
      type: "POST",
      url: form.attr("action"),
      data: new FormData(form[0]),
      dataType: "json",
      contentType: false,
      processData: false,
      headers: { "X-CSRFToken": this.config.csrfToken },
      beforeSend: () => this.setFormLoading(true),
      success: (response) => this.handleFormSuccess(response),
      error: () => this.handleFormError(),
    });
  }

  /**
   * Set form loading state
   */
  setFormLoading(isLoading) {
    const cancelBtn = $(this.selectors.cancelBtn);
    const submitBtn = $(this.selectors.submitBtn);

    if (isLoading) {
      cancelBtn.removeClass("d-inline-block").addClass("d-none");
      submitBtn
        .html("<i class='fas fa-spinner fa-pulse'></i> Saving")
        .attr("type", "button");
    } else {
      cancelBtn.removeClass("d-none").addClass("d-inline-block");
      submitBtn.text("Save").attr("type", "submit");
    }
  }

  /**
   * Handle form success response
   */
  handleFormSuccess(response) {
    this.setFormLoading(false);

    const feedback = this.generateAlert(response.success, response.sms);
    this.scrollToTop(this.selectors.canvas);
    $(`${this.selectors.form} .formsms`).html(feedback);

    if (response.update_success) {
      $(this.selectors.shopsDiv).load(
        `${location.href} ${this.selectors.shopsDiv}`
      );
      this.scrollToTop("html, body");
    } else if (response.success) {
      $(this.selectors.form)[0].reset();
      this.table.draw();
    }
  }

  /**
   * Handle form error
   */
  handleFormError() {
    this.setFormLoading(false);

    const feedback = this.generateAlert(false, "Unknown error, reload & try");
    this.scrollToTop(this.selectors.canvas);
    $(`${this.selectors.form} .formsms`).html(feedback);
  }

  /**
   * Scroll to top utility
   */
  scrollToTop(selector) {
    if (selector.includes("canvas")) {
      $(`${selector} .offcanvas-body`).animate({ scrollTop: 0 }, "slow");
    } else {
      $(selector).animate({ scrollTop: 0 }, "slow");
    }
  }

  /**
   * Date range management
   */
  getDateRange() {
    const minDateStr = $(this.selectors.minDate).val();
    const maxDateStr = $(this.selectors.maxDate).val();

    try {
      let dtStartUtc = null;
      let dtEndUtc = null;

      if (minDateStr) {
        const startDateLocal = new Date(`${minDateStr}T00:00:00.000`);
        if (isNaN(startDateLocal.getTime())) {
          throw new Error("Invalid start date format");
        }
        dtStartUtc = startDateLocal.toISOString();
      }

      if (maxDateStr) {
        const endDateLocal = new Date(`${maxDateStr}T23:59:59.999`);
        if (isNaN(endDateLocal.getTime())) {
          throw new Error("Invalid end date format");
        }
        dtEndUtc = endDateLocal.toISOString();
      }

      // Cache the results
      this.config.dateCache.start = dtStartUtc;
      this.config.dateCache.end = dtEndUtc;

      return { start: dtStartUtc, end: dtEndUtc };
    } catch (error) {
      console.error("Date processing error:", error);
      return { start: null, end: null };
    }
  }

  /**
   * Clear date filters
   */
  clearDates() {
    $(this.selectors.minDate).val("");
    $(this.selectors.maxDate).val("");
    this.config.dateCache.start = null;
    this.config.dateCache.end = null;
  }

  /**
   * Setup DataTable
   */
  setupTable() {
    // Clone header for filters
    $(`${this.selectors.table} thead tr`)
      .clone(true)
      .attr("class", "filters")
      .appendTo(`${this.selectors.table} thead`);

    this.table = $(this.selectors.table).DataTable({
      fixedHeader: true,
      processing: true,
      serverSide: true,
      ajax: this.getAjaxConfig(),
      columns: this.getColumnConfig(),
      order: [[3, "desc"]],
      paging: true,
      lengthMenu: [
        [10, 20, 40, 50, 100, 200],
        [10, 20, 40, 50, 100, 200],
      ],
      pageLength: 10,
      lengthChange: true,
      autoWidth: true,
      searching: true,
      bInfo: true,
      bSort: true,
      orderCellsTop: true,
      columnDefs: this.getColumnDefs(),
      dom: "lBfrtip",
      buttons: this.getButtonConfig(),
      initComplete: () => this.initTableFilters(),
      language: {
        lengthMenu: "Show _MENU_ rows",
        info: "Showing _START_ to _END_ of _TOTAL_ rows",
        infoEmpty: "Showing 0 to 0 of 0 rows",
        infoFiltered: "(filtered from _MAX_ total rows)",
        search: "Search:",
        paginate: {
          first: "First",
          last: "Last",
          next: "Next",
          previous: "Prev",
        },
      },
    });
  }

  /**
   * Get AJAX configuration for DataTable
   */
  getAjaxConfig() {
    return {
      url: $(this.selectors.shopsListUrl).val(),
      type: "POST",
      data: (d) => {
        const dateRange = this.getDateRange();
        d.startdate = dateRange.start;
        d.enddate = dateRange.end;
      },
      dataType: "json",
      headers: { "X-CSRFToken": this.config.csrfToken },
    };
  }

  /**
   * Get column configuration
   */
  getColumnConfig() {
    return [
      { data: "count" },
      { data: "names" },
      { data: "abbrev" },
      { data: "regdate" },
      { data: "users_count" },
      { data: "items_count" },
      { data: "networth" },
    ];
  }

  /**
   * Get column definitions
   */
  getColumnDefs() {
    return [
      {
        targets: 0,
        orderable: false,
      },
      {
        targets: 1,
        createdCell: (cell, cellData, rowData) => {
          const cellContent = `
            <a href="${rowData.info}" class="shop-link">
              <div class="shop-info">
                <div class="shop-avatar">
                  <i class="fas fa-store"></i>
                </div>
                <span>${rowData.names}</span>
              </div>
            </a>
          `;
          $(cell).html(cellContent).addClass("ellipsis text-start");
        },
      },
      {
        targets: 6,
        createdCell: (cell) => $(cell).addClass("text-end pe-3"),
      },
    ];
  }

  /**
   * Get button configuration for DataTable
   */
  getButtonConfig() {
    const baseConfig = {
      className: "btn btn-extra text-white",
      title: "Shops - FrankApp",
      exportOptions: { columns: this.config.columnIndices },
    };

    return [
      {
        extend: "copy",
        text: "<i class='fas fa-clone'></i>",
        titleAttr: "Copy",
        ...baseConfig,
      },
      {
        extend: "pdf",
        text: "<i class='fas fa-file-pdf'></i>",
        titleAttr: "Export to PDF",
        filename: "shops-frankapp",
        orientation: "portrait",
        pageSize: "A4",
        footer: true,
        exportOptions: {
          ...baseConfig.exportOptions,
          search: "applied",
          order: "applied",
        },
        tableHeader: { alignment: "center" },
        customize: this.customizePDF.bind(this),
        ...baseConfig,
      },
      {
        extend: "excel",
        text: "<i class='fas fa-file-excel'></i>",
        titleAttr: "Export to Excel",
        ...baseConfig,
      },
      {
        extend: "print",
        text: "<i class='fas fa-print'></i>",
        titleAttr: "Print",
        orientation: "portrait",
        pageSize: "A4",
        footer: true,
        exportOptions: {
          ...baseConfig.exportOptions,
          search: "applied",
          order: "applied",
        },
        tableHeader: { alignment: "center" },
        customize: this.customizePrint.bind(this),
        ...baseConfig,
      },
    ];
  }

  /**
   * Customize PDF export
   */
  customizePDF(doc) {
    doc.styles.tableHeader.alignment = "center";
    doc.styles.tableBodyOdd.alignment = "center";
    doc.styles.tableBodyEven.alignment = "center";
    doc.styles.tableHeader.fontSize = 7;
    doc.defaultStyle.fontSize = 6;
    doc.content[1].table.widths = Array(doc.content[1].table.body[1].length + 1)
      .join("*")
      .split("");

    const body = doc.content[1].table.body;
    for (let i = 1; i < body.length; i++) {
      const row = doc.content[1].table.body[i];

      // Configure cell alignments and padding
      const cellConfigs = [
        { alignment: "center", margin: [3, 0, 0, 0] },
        { alignment: "left" },
        { alignment: "left" },
        { alignment: "center" },
        { alignment: "center" },
        { alignment: "center" },
        { alignment: "right", margin: [0, 0, 3, 0] },
      ];

      cellConfigs.forEach((config, j) => {
        if (row[j]) {
          Object.assign(row[j], config);
          row[j].style = "vertical-align: middle;";
        }
      });
    }
  }

  /**
   * Customize print output
   */
  customizePrint(win) {
    $(win.document.body).css("font-size", "11pt");
    $(win.document.body)
      .find("table")
      .addClass("compact")
      .css("font-size", "inherit");
  }

  /**
   * Initialize table filters
   */
  initTableFilters() {
    const api = this.table;

    api
      .columns(this.config.columnIndices)
      .eq(0)
      .each((colIdx) => {
        const cell = $(".filters th").eq(
          $(api.column(colIdx).header()).index()
        );
        cell.addClass("bg-white");

        if (colIdx === 0) {
          cell.html("");
        } else if (colIdx === 3) {
          const calendar = `
            <button type="button" class="btn btn-sm btn-primary text-white" 
                    data-bs-toggle="modal" data-bs-target="#date_filter_modal">
              <i class="fas fa-calendar-alt"></i>
            </button>
          `;
          cell.html(calendar);
        } else {
          cell.html(
            "<input type='text' class='text-charcoal' placeholder='Filter..'/>"
          );
          this.setupColumnFilter(cell, api, colIdx);
        }
      });
  }

  /**
   * Setup individual column filter
   */
  setupColumnFilter(cell, api, colIdx) {
    const input = $("input", cell);

    input.off("keyup change").on("keyup change", function (e) {
      e.stopPropagation();
      $(this).attr("title", $(this).val());

      const regexr = "{search}";
      const cursorPosition = this.selectionStart;

      api
        .column(colIdx)
        .search(
          this.value !== "" ? regexr.replace("{search}", this.value) : "",
          this.value !== "",
          this.value === ""
        )
        .draw();

      $(this).focus()[0].setSelectionRange(cursorPosition, cursorPosition);
    });
  }

  /**
   * Setup all event handlers
   */
  setupEventHandlers() {
    this.setupSearchHandler();
    this.setupFilterHandlers();
    this.setupDeleteHandler();
  }

  /**
   * Setup search handler
   */
  setupSearchHandler() {
    $(this.selectors.searchInput)
      .off("keyup")
      .on("keyup", () => {
        this.table.search($(this.selectors.searchInput).val()).draw();
      });
  }

  /**
   * Setup filter handlers
   */
  setupFilterHandlers() {
    $(this.selectors.clearFilter)
      .off("click")
      .on("click", (e) => {
        e.preventDefault();
        $(this.selectors.searchInput).val("");
        this.clearDates();
        $('.filters input[type="text"]').val("");
        $(".filters select").val("");
        this.table.search("").columns().search("").draw();
      });

    $(this.selectors.dateClear)
      .off("click")
      .on("click", () => this.clearDates());

    $(this.selectors.dateFilterBtn)
      .off("click")
      .on("click", () => this.table.draw());
  }

  /**
   * Setup delete handler
   */
  setupDeleteHandler() {
    $(this.selectors.confirmDeleteBtn)
      .off("click")
      .on("click", (e) => {
        e.preventDefault();
        if (!this.config.deletingState) {
          this.handleDelete();
        }
      });
  }

  /**
   * Handle delete operation
   */
  handleDelete() {
    const formData = new FormData();
    formData.append("delete_shop", $(this.selectors.shopId).val());

    $.ajax({
      type: "POST",
      url: $(this.selectors.form).attr("action"),
      data: formData,
      dataType: "json",
      contentType: false,
      processData: false,
      headers: { "X-CSRFToken": this.config.csrfToken },
      beforeSend: () => this.setDeleteLoading(true),
      success: (response) => this.handleDeleteSuccess(response),
      error: (xhr, status, error) => {
        console.error("Delete error:", error);
        this.setDeleteLoading(false);
      },
    });
  }

  /**
   * Set delete loading state
   */
  setDeleteLoading(isLoading) {
    this.config.deletingState = isLoading;
    const cancelBtn = $(this.selectors.cancelDeleteBtn);
    const confirmBtn = $(this.selectors.confirmDeleteBtn);

    if (isLoading) {
      cancelBtn.removeClass("d-inline-block").addClass("d-none");
      confirmBtn.html("<i class='fas fa-spinner fa-pulse'></i>");
    } else {
      cancelBtn.removeClass("d-none").addClass("d-inline-block");
      confirmBtn.html("<i class='fas fa-check-circle'></i> Yes");
    }
  }

  /**
   * Handle delete success
   */
  handleDeleteSuccess(response) {
    this.config.deletingState = false;

    if (response.success) {
      alert("The shop has been deleted permanently..!");
      window.location.href = response.url;
    } else {
      this.setDeleteLoading(false);
      const feedback = this.generateAlert(response.success, response.sms);
      $(`${this.selectors.deleteModal} .formsms`).html(feedback);
    }
  }
}

// Initialize the application when DOM is ready
$(function () {
  new ShopsManager();
});
