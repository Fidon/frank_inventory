$(function () {
  const CSRF_TOKEN = document
    .querySelector('meta[name="csrf-token"]')
    .getAttribute("content");
  const COLUMN_INDICES = [0, 1, 2, 3];
  const DATE_CACHE = { start: null, end: null };

  function generate_errorsms(status, sms) {
    return `<div class="alert alert-${
      status ? "success" : "danger"
    } alert-dismissible fade show px-2 m-0 d-block w-100"><i class='fas fa-${status ? "check" : "exclamation"}-circle'></i> ${sms} <button type="button" class="btn-close d-inline-block" data-bs-dismiss="alert"></button></div>`;
  }

  // New shop registration & update
  $("#new_shop_form").submit(function (e) {
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
        $("#shop_cancel_btn").removeClass("d-inline-block").addClass("d-none");
        $("#shop_submit_btn")
          .html("<i class='fas fa-spinner fa-pulse'></i> Saving")
          .attr("type", "button");
      },
      success: function (response) {
        $("#shop_cancel_btn").removeClass("d-none").addClass("d-inline-block");
        $("#shop_submit_btn").text("Save").attr("type", "submit");

        var fdback = generate_errorsms(response.success, response.sms);

        $("#new_shop_canvas .offcanvas-body").animate({ scrollTop: 0 }, "slow");
        $("#new_shop_form .formsms").html(fdback);

        if (response.update_success) {
          $("#shop_div").load(location.href + " #shop_div");
          $("html, body").animate({ scrollTop: 0 }, "slow");
        } else if (response.success) {
          $("#new_shop_form")[0].reset();
          shops_table.draw();
        }
      },
      error: function (xhr, status, error) {
        $("#shop_cancel_btn").removeClass("d-none").addClass("d-inline-block");
        $("#shop_submit_btn").text("Save").attr("type", "submit");
        var fdback = generate_errorsms(false, "Unknown error, reload & try");
        $("#new_shop_canvas .offcanvas-body").animate({ scrollTop: 0 }, "slow");
        $("#new_shop_form .formsms").html(fdback);
      },
    });
  });

  function getDateRange() {
    const minDateStr = $("#min_date").val();
    const maxDateStr = $("#max_date").val();

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
      DATE_CACHE.start = dtStartUtc;
      DATE_CACHE.end = dtEndUtc;

      return { start: dtStartUtc, end: dtEndUtc };
    } catch (error) {
      console.error("Date processing error:", error);
      return { start: null, end: null };
    }
  }

  function clearDates() {
    $("#min_date").val("");
    $("#max_date").val("");
    DATE_CACHE.start = null;
    DATE_CACHE.end = null;
  }

  // Shops table initialization
  $("#shops_table thead tr")
    .clone(true)
    .attr("class", "filters")
    .appendTo("#shops_table thead");

  var shops_table = $("#shops_table").DataTable({
    fixedHeader: true,
    processing: true,
    serverSide: true,
    ajax: {
      url: $("#users_list_url").val(),
      type: "POST",
      data: function (d) {
        const dateRange = getDateRange();
        d.startdate = dateRange.start;
        d.enddate = dateRange.end;
      },
      dataType: "json",
      headers: { "X-CSRFToken": CSRF_TOKEN },
    },
    columns: [
      { data: "count" },
      { data: "names" },
      { data: "abbrev" },
      { data: "regdate" },
    ],
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
    columnDefs: [
      {
        targets: 0,
        orderable: false,
      },
      {
        targets: 1,
        className: "ellipsis text-start",
        createdCell: function (cell, cellData, rowData, rowIndex, colIndex) {
          var cell_content =
            `<a href="${rowData.info}" class="shop-link">` +
            `<div class="shop-info">` +
            `<div class="shop-avatar">` +
            `<i class="fas fa-store"></i></div>` +
            `<span>${rowData.names}</span></div></a>`;
          $(cell).html(cell_content);
        },
      },
    ],
    dom: "lBfrtip",
    buttons: [
      {
        // Copy button
        extend: "copy",
        text: "<i class='fas fa-clone'></i>",
        className: "btn btn-extra text-white",
        titleAttr: "Copy",
        title: "Shops - FrankApp",
        exportOptions: {
          columns: COLUMN_INDICES,
        },
      },
      {
        // PDF button
        extend: "pdf",
        text: "<i class='fas fa-file-pdf'></i>",
        className: "btn btn-extra text-white",
        titleAttr: "Export to PDF",
        title: "Shops - FrankApp",
        filename: "shops-frankapp",
        orientation: "portrait",
        pageSize: "A4",
        footer: true,
        exportOptions: {
          columns: COLUMN_INDICES,
          search: "applied",
          order: "applied",
        },
        tableHeader: {
          alignment: "center",
        },
        customize: function (doc) {
          doc.styles.tableHeader.alignment = "center";
          doc.styles.tableBodyOdd.alignment = "center";
          doc.styles.tableBodyEven.alignment = "center";
          doc.styles.tableHeader.fontSize = 7;
          doc.defaultStyle.fontSize = 6;
          doc.content[1].table.widths = Array(
            doc.content[1].table.body[1].length + 1
          )
            .join("*")
            .split("");

          var body = doc.content[1].table.body;
          for (i = 1; i < body.length; i++) {
            doc.content[1].table.body[i][0].margin = [3, 0, 0, 0];
            doc.content[1].table.body[i][0].alignment = "center";
            doc.content[1].table.body[i][1].alignment = "left";
            doc.content[1].table.body[i][2].alignment = "left";
            doc.content[1].table.body[i][3].alignment = "center";
            doc.content[1].table.body[i][4].alignment = "center";
            doc.content[1].table.body[i][5].alignment = "center";
            doc.content[1].table.body[i][5].margin = [0, 0, 3, 0];

            for (let j = 0; j < body[i].length; j++) {
              body[i][j].style = "vertical-align: middle;";
            }
          }
        },
      },
      {
        // Export to excel button
        extend: "excel",
        text: "<i class='fas fa-file-excel'></i>",
        className: "btn btn-extra text-white",
        titleAttr: "Export to Excel",
        title: "Shops - FrankApp",
        exportOptions: {
          columns: COLUMN_INDICES,
        },
      },
      {
        // Print button
        extend: "print",
        text: "<i class='fas fa-print'></i>",
        className: "btn btn-extra text-white",
        title: "Shops - FrankApp",
        orientation: "portrait",
        pageSize: "A4",
        titleAttr: "Print",
        footer: true,
        exportOptions: {
          columns: COLUMN_INDICES,
          search: "applied",
          order: "applied",
        },
        tableHeader: {
          alignment: "center",
        },
        customize: function (win) {
          $(win.document.body).css("font-size", "11pt");
          $(win.document.body)
            .find("table")
            .addClass("compact")
            .css("font-size", "inherit");
        },
      },
    ],
    initComplete: function () {
      var api = this.api();
      api
        .columns(COLUMN_INDICES)
        .eq(0)
        .each(function (colIdx) {
          var cell = $(".filters th").eq(
            $(api.column(colIdx).header()).index()
          );
          cell.addClass("bg-white");
          if (colIdx == 3) {
            var calendar = `<button type="button" class="btn btn-sm btn-primary text-white" data-bs-toggle="modal" data-bs-target="#date_filter_modal"><i class="fas fa-calendar-alt"></i></button>`;
            cell.html(calendar);
          } else if (colIdx == 0) {
            cell.html("");
          } else {
            $(cell).html(
              "<input type='text' class='text-charcoal' placeholder='Filter..'/>"
            );
            $(
              "input",
              $(".filters th").eq($(api.column(colIdx).header()).index())
            )
              .off("keyup change")
              .on("keyup change", function (e) {
                e.stopPropagation();
                $(this).attr("title", $(this).val());
                var regexr = "{search}";
                var cursorPosition = this.selectionStart;
                api
                  .column(colIdx)
                  .search(
                    this.value != ""
                      ? regexr.replace("{search}", this.value)
                      : "",
                    this.value != "",
                    this.value == ""
                  )
                  .draw();
                $(this)
                  .focus()[0]
                  .setSelectionRange(cursorPosition, cursorPosition);
              });
          }
        });
    },
  });

  // Event handlers on user search and date filtering
  $("#shops_search")
    .off("keyup")
    .on("keyup", function () {
      shops_table.search($(this).val()).draw();
    });

  $("#shops_filter_clear")
    .off("click")
    .on("click", function (e) {
      e.preventDefault();
      $("#shops_search").val("");
      clearDates();
      $(".filters input[type='text']").val("");
      $(".filters select").val("");
      shops_table.columns().search("").draw();
    });

  $("#date_clear")
    .off("click")
    .on("click", function () {
      clearDates();
    });

  $("#date_filter_btn")
    .off("click")
    .on("click", function () {
      shops_table.draw();
    });

  // Delete confirmation modal
  var btn_deleting = false;
  $("#confirm_delete_btn").click(function (e) {
    e.preventDefault();
    if (btn_deleting == false) {
      var formData = new FormData();
      formData.append("delete_shop", $("#get_shop_id").val());

      $.ajax({
        type: "POST",
        url: $("#new_shop_form").attr("action"),
        data: formData,
        dataType: "json",
        contentType: false,
        processData: false,
        headers: {
          "X-CSRFToken": CSRF_TOKEN,
        },
        beforeSend: function () {
          btn_deleting = true;
          $("#cancel_delete_btn")
            .removeClass("d-inline-block")
            .addClass("d-none");
          $("#confirm_delete_btn").html(
            "<i class='fas fa-spinner fa-pulse'></i>"
          );
        },
        success: function (response) {
          btn_deleting = false;
          if (response.success) {
            window.alert("The shop has been deleted permanently..!");
            window.location.href = response.url;
          } else {
            $("#cancel_delete_btn")
              .removeClass("d-none")
              .addClass("d-inline-block");
            $("#confirm_delete_btn").html(
              "<i class='fas fa-check-circle'></i> Yes"
            );

            var fdback = generate_errorsms(response.success, response.sms);

            $("#confirm_delete_modal .formsms").html(fdback);
          }
        },
        error: function (xhr, status, error) {
          console.log(error);
        },
      });
    }
  });
});
