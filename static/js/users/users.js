$(function () {
  const CSRF_TOKEN = document
    .querySelector('meta[name="csrf-token"]')
    .getAttribute("content");
  const COLUMN_INDICES = [0, 1, 2, 3, 4, 5];
  const DATE_CACHE = { start: null, end: null };

  function generate_errorsms(status, sms) {
    return `<div class="alert alert-${
      status ? "success" : "danger"
    } alert-dismissible fade show px-2 m-0 d-block w-100"><i class='fas fa-${status ? "check" : "exclamation"}-circle'></i> ${sms} <button type="button" class="btn-close d-inline-block" data-bs-dismiss="alert"></button></div>`;
  }

  // Handle user registration and update form submission
  $("#new_user_form").submit(function (e) {
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
        $("#user_cancel_btn").removeClass("d-inline-block").addClass("d-none");
        $("#user_submit_btn")
          .html("<i class='fas fa-spinner fa-pulse'></i> Saving")
          .attr("type", "button");
      },
      success: function (response) {
        $("#user_cancel_btn").removeClass("d-none").addClass("d-inline-block");
        $("#user_submit_btn").text("Save").attr("type", "submit");

        var fdback = generate_errorsms(response.success, response.sms);

        $("#new_user_canvas .offcanvas-body").animate({ scrollTop: 0 }, "slow");
        $("#new_user_form .formsms").html(fdback);

        if (response.update_success) {
          $("#user_div").load(location.href + " #user_div");
          $("#update_user_canvas").offcanvas("hide");
          $("html, body").animate({ scrollTop: 0 }, "slow");
        } else if (response.success) {
          $("#new_user_form")[0].reset();
          $("#reg_phone").val("+255");
          users_table.draw();
        }
      },
      error: function (xhr, status, error) {
        $("#user_cancel_btn").removeClass("d-none").addClass("d-inline-block");
        $("#user_submit_btn").text("Save").attr("type", "submit");
        var fdback = generate_errorsms(false, "Unknown error, reload & try");
        $("#new_user_canvas .offcanvas-body").animate({ scrollTop: 0 }, "slow");
        $("#new_user_form .formsms").html(fdback);
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
      // Return nulls if date processing fails
      return { start: null, end: null };
    }
  }

  function clearDates() {
    $("#min_date").val("");
    $("#max_date").val("");
    DATE_CACHE.start = null;
    DATE_CACHE.end = null;
  }

  // Users table initialization
  $("#users_table thead tr")
    .clone(true)
    .attr("class", "filters")
    .appendTo("#users_table thead");

  var users_table = $("#users_table").DataTable({
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
      { data: "fullname" },
      { data: "username" },
      { data: "regdate" },
      { data: "phone" },
      { data: "status" },
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
        targets: [0, 4],
        orderable: false,
      },
      {
        targets: 1,
        className: "ellipsis text-start",
        createdCell: function (cell, cellData, rowData, rowIndex, colIndex) {
          var cell_content =
            `<a href="${rowData.info}" class="user-link">` +
            `<div class="user-info">` +
            `<div class="user-avatar">` +
            `<i class="fas fa-user"></i></div>` +
            `<span>${rowData.fullname}</span></div></a>`;
          $(cell).html(cell_content);
        },
      },
      {
        targets: 2,
        className: "text-start",
      },
      {
        targets: 5,
        createdCell: function (cell, cellData, rowData, rowIndex, colIndex) {
          var cell_content = `<div class="status"></div>`;
          if (rowData.status == "active")
            cell_content = `<div class="status active"></div>`;
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
        title: "Users - FrankApp",
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
        title: "Users - FrankApp",
        filename: "users-frankapp",
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
        title: "Users - FrankApp",
        exportOptions: {
          columns: COLUMN_INDICES,
        },
      },
      {
        // Print button
        extend: "print",
        text: "<i class='fas fa-print'></i>",
        className: "btn btn-extra text-white",
        title: "Users - FrankApp",
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
          } else if (colIdx == 5) {
            var select = document.createElement("select");
            select.className = "select-filter text-charcoal float-start";
            select.innerHTML =
              `<option value="">All</option>` +
              `<option value="active">Active</option>` +
              `<option value="inactive">Blocked</option>`;
            cell.html(select);
            $(select).on("change", function () {
              api.column(colIdx).search($(this).val()).draw();
            });
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
  $("#users_search")
    .off("keyup")
    .on("keyup", function () {
      users_table.search($(this).val()).draw();
    });

  $("#users_filter_clear")
    .off("click")
    .on("click", function (e) {
      e.preventDefault();
      $("#users_search").val("");
      clearDates();
      $(".filters input[type='text']").val("");
      $(".filters select").val("");
      users_table.columns().search("").draw();
    });

  $("#date_clear")
    .off("click")
    .on("click", function () {
      clearDates();
    });

  $("#date_filter_btn")
    .off("click")
    .on("click", function () {
      users_table.draw();
    });

  var btn_blocking = false;
  var btn_deleting = false;
  var btn_resetting = false;
  $("#user_blockbtn").click(function (e) {
    e.preventDefault();
    if (btn_blocking == false) {
      var btn_html = $(this).html();
      var formdata = new FormData();
      formdata.append("block_user", parseInt($("#get_user_id").val()));

      $.ajax({
        type: "POST",
        url: $("#new_user_form").attr("action"),
        data: formdata,
        dataType: "json",
        contentType: false,
        processData: false,
        headers: {
          "X-CSRFToken": CSRF_TOKEN,
        },
        beforeSend: function () {
          btn_blocking = true;
          $("#user_blockbtn").html(
            "<i class='fas fa-spinner fa-pulse'></i>Updating"
          );
        },
        success: function (response) {
          btn_blocking = false;
          if (response.success) {
            location.reload();
          } else {
            $("#user_blockbtn").html(btn_html);
            window.alert("Operation failed, reload and try again");
          }
        },
        error: function (xhr, status, error) {
          console.log(error);
        },
      });
    }
  });

  $("#confirm_delete_btn").click(function (e) {
    e.preventDefault();
    if (btn_deleting == false) {
      var formData = new FormData();
      formData.append("delete_user", $("#get_user_id").val());

      $.ajax({
        type: "POST",
        url: $("#new_user_form").attr("action"),
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
            window.alert("User account deleted permanently..!");
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

  $("#confirm_reset_btn").click(function (e) {
    e.preventDefault();
    if (btn_resetting == false) {
      var formData = new FormData();
      formData.append("reset_password", $("#get_user_id").val());

      $.ajax({
        type: "POST",
        url: $("#new_user_form").attr("action"),
        data: formData,
        dataType: "json",
        contentType: false,
        processData: false,
        headers: {
          "X-CSRFToken": CSRF_TOKEN,
        },
        beforeSend: function () {
          btn_resetting = true;
          $("#cancel_reset_btn")
            .removeClass("d-inline-block")
            .addClass("d-none");
          $("#confirm_reset_btn").html(
            "<i class='fas fa-spinner fa-pulse'></i>"
          );
        },
        success: function (response) {
          btn_resetting = false;
          if (response.success) {
            $("#confirm_reset_btn")
              .removeClass("d-inline-block")
              .addClass("d-none");
            $("#confirm_reset_modal").modal("hide");
            window.alert("Password has been reset to default.");
          } else {
            $("#cancel_reset_btn")
              .removeClass("d-none")
              .addClass("d-inline-block");
            $("#confirm_reset_btn").html(
              "<i class='fas fa-check-circle'></i> Yes"
            );

            var fdback = generate_errorsms(response.success, response.sms);

            $("#confirm_reset_modal .formsms").html(fdback);
          }
        },
        error: function (xhr, status, error) {
          console.log(error);
        },
      });
    }
  });
});
