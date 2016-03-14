
var editing_order = false;
var dragging = false;

function order_button_click(node)
{
    var rows, form;

    form = $("#reorderform");
    rows = $("#patchlist").get(0).tBodies[0].rows;

    if (rows.length < 1)
        return;

    if (editing_order) {

        /* disable the save button */
        node.disabled = true;

        /* add input elements as the sequence of patches */
        for (var i = 0; i < rows.length; i++) {
            form.append('<input type="hidden" name="neworder" value="' +
                    row_to_patch_id(rows[i]) + '"/>');
        }

        form.get(0).submit();
    } else {

        /* store the first order value */
        start_order = row_to_patch_id(rows[0]);
        $("input[name='order_start']").attr("value", start_order);

        /* update buttons */
        node.setAttribute("value", "Save order");
        $("#reorder\\-cancel").css("display", "inline");

        /* show help text */
        $("#reorderhelp").text('Drag & drop rows to reorder');

        /* enable drag & drop on the patches list */
        $("#patchlist").tableDnD({
            onDragClass: 'dragging',
            onDragStart: function() { dragging = true; },
            onDrop: function() { dragging = false; }
        });

        /* replace zebra striping with hover */
        $("#patchlist tbody tr").css("background", "inherit");
        $("#patchlist tbody tr").hover(drag_hover_in, drag_hover_out);
    }

    editing_order = !editing_order;
}

function order_cancel_click(node)
{
    node.form.submit();
}

/* dragging helper functions */
function drag_hover_in()
{
    if (!dragging)
        $(this).addClass("draghover");
}
function drag_hover_out()
{
    $(this).removeClass("draghover");
}

function row_to_patch_id(node)
{
    var id_str, i;

    id_str = node.getAttribute("id");

    i = id_str.indexOf(':');
    if (i == -1)
        return null;

    return id_str.substring(i + 1);
}

function confirm_delete(type, name)
{
    return confirm("Are you sure you want to delete the " + type +
                   " '" + name + "'?");
}
