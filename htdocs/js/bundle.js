function parse_patch_id(id_str)
{
    var i;

    i = id_str.indexOf(':');
    if (i == -1)
        return null;

    return id_str.substring(i + 1);
}

function bundle_handle_drop(table, row)
{
    var relative, relation, current;
    var relative_id, current_id;

    current = $(row);
    relative = $(current).prev();
    relation = 'after';

    /* if we have no previous row, position ourselves before the next
     * row instead */
    if (!relative.length) {
        relative = current.next();
        relation = 'before';

        if (!relative)
            return;
    }

    current_id = parse_patch_id(current.attr('id'));
    relative_id = parse_patch_id(relative.attr('id'));

    alert("put patch " + current_id + " " + relation + " " + relative_id);
}

$(document).ready(function() {
    $("#patchlist").tableDnD({
        onDrop: bundle_handle_drop
    });
});
