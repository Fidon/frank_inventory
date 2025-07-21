class CripsManager {
  constructor() {
    this.config = {
      columnIndices: [0, 1, 2, 3, 4, 5, 6],
      dateCache: { start: null, end: null },
      csrfToken: this.getCSRFToken(),
      deletingState: false,
    };

    this.selectors = {
      form: "#new_crips_form",
      table: "#crips_table",
      canvas: "#new_crips_canvas",
      cancelBtn: "#crips_cancel_btn",
      submitBtn: "#crips_submit_btn",
      searchInput: "#crips_search",
      clearFilter: "#crips_filter_clear",
      minDate: "#min_date",
      maxDate: "#max_date",
      dateClear: "#date_clear",
      dateFilterBtn: "#date_filter_btn",
      confirmDeleteBtn: "#confirm_delete_btn",
      cancelDeleteBtn: "#cancel_delete_btn",
      cripsDiv: "#crips_div",
      cripsListUrl: "#crips_list_url",
      cripsId: "#get_crips_id",
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
   * Format currency for display
   */
  formatCurrency(num) {
    return (
      num.toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }) + " TZS"
    );
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
      $(this.selectors.cripsDiv).load(
        `${location.href} ${this.selectors.cripsDiv}`
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
      order: [[1, "desc"]],
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
      footerCallback: this.getFooterCallback(),
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
      url: $(this.selectors.cripsListUrl).val(),
      type: "POST",
      data: (d) => {
        const dateRange = this.getDateRange();
        d.startdate = dateRange.start;
        d.enddate = dateRange.end;
      },
      dataType: "json",
      headers: { "X-CSRFToken": this.config.csrfToken },
      dataSrc: (json) => {
        $(`${this.selectors.table} tfoot tr:eq(1) th:eq(5)`)
          .html(json.grand_total)
          .addClass("text-end pe-3");
        return json.data;
      },
    };
  }

  /**
   * Get column configuration
   */
  getColumnConfig() {
    return [
      { data: "count" },
      { data: "regdate" },
      { data: "name" },
      { data: "qty" },
      { data: "price" },
      { data: "amount" },
      { data: "info" },
    ];
  }

  /**
   * Get column definitions
   */
  getColumnDefs() {
    return [
      {
        targets: [0, 6],
        orderable: false,
      },
      {
        targets: [3, 4, 5],
        createdCell: (cell) => $(cell).addClass("text-end pe-3"),
      },
      {
        targets: 6,
        createdCell: (cell, cellData, rowData) => {
          const cellContent = `<a href="${rowData.info}" class="btn btn-success btn-sm">View</a>`;
          $(cell)
            .html(cellContent)
            .addClass("align-middle text-nowrap text-center");
        },
      },
    ];
  }

  /**
   * Get button configuration for DataTable
   */
  getButtonConfig() {
    const baseConfig = {
      className: "btn btn-extra text-white",
      title: "Crips - FrankApp",
      exportOptions: { columns: [0, 1, 2, 3, 4, 5] },
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
        filename: "crips-frankapp",
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
    doc.styles.tableHeader.fontSize = 11;
    doc.defaultStyle.fontSize = 11;
    doc.content[1].table.widths = Array(doc.content[1].table.body[1].length + 1)
      .join("*")
      .split("");

    const body = doc.content[1].table.body;
    for (let i = 1; i < body.length; i++) {
      const row = doc.content[1].table.body[i];

      // Configure cell alignments and padding
      const cellConfigs = [
        { alignment: "center", margin: [3, 0, 0, 0] },
        { alignment: "center" },
        { alignment: "center" },
        { alignment: "right", padding: [0, 10, 0, 0] },
        { alignment: "right", padding: [0, 10, 0, 0] },
        { alignment: "right", padding: [0, 10, 0, 0], margin: [0, 0, 3, 0] },
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
   * Get footer callback for DataTable
   */
  getFooterCallback() {
    return (row, data, start, end, display) => {
      const api = this.table;
      const intVal = (i) =>
        typeof i === "string"
          ? i.replace(/[\s,]/g, "").replace(/TZS/g, "") * 1
          : typeof i === "number"
          ? i
          : 0;

      const amountTotal = api
        .column(5)
        .data()
        .reduce((a, b) => intVal(a) + intVal(b), 0);

      const pageTotalValue = this.formatCurrency(amountTotal);
      $(api.table().footer())
        .find("tr:eq(0) th:eq(5)")
        .html(pageTotalValue)
        .addClass("text-end pe-3");
    };
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

        if (colIdx === 0 || colIdx === 6) {
          cell.html("");
        } else if (colIdx === 1) {
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
    formData.append("delete_crips", $(this.selectors.cripsId).val());

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
      alert("Record has been deleted permanently..!");
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
  new CripsManager();
});
