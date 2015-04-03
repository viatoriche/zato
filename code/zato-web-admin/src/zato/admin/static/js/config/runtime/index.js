
// /////////////////////////////////////////////////////////////////////////////

$.fn.zato.data_table.RuntimeConfigItem = new Class({
    toString: function() {
        var s = '<RuntimeConfigItem id:{0} name:{1} is_active:{2}';
        return String.format(s, this.id ? this.id : '(none)',
                                this.name ? this.name : '(none)',
                                this.is_active ? this.is_active : '(none)');
    }
});

// /////////////////////////////////////////////////////////////////////////////

$(document).ready(function() {
    $('#data-table').tablesorter();
    $.fn.zato.data_table.class_ = $.fn.zato.data_table.RuntimeConfigItem;
    $.fn.zato.data_table.new_row_func = $.fn.zato.config.runtime.data_table.new_row;
    $.fn.zato.data_table.parse();
    $.fn.zato.data_table.setup_forms(['name']);
})

$.fn.zato.config.runtime.create = function() {
    $.fn.zato.data_table._create_edit('create', 'Create a new config file', null);
}

$.fn.zato.config.runtime.data_table.new_row = function(item, data, include_tr) {
    var row = '';

    if(include_tr) {
        row += String.format("<tr id='tr_{0}' class='updated'>", item.id);
    }

    var is_active = item.is_active == true;
    var cluster_id = $(document).getUrlParam('cluster');

    row += "<td class='numbering'>&nbsp;</td>";
    row += "<td class='impexp'><input type='checkbox' /></td>";
    row += String.format('<td>{0}</td>', item.name);
    row += String.format('<td>{0}</td>', String.format("<a href=''>./details/{0}/cluster/{1}/</a>", item.name, $('#cluster_id').val()));
    row += String.format('<td>{0}</td>', String.format("<a href='javascript:$.fn.zato.config.runtime.delete_({0});'>Delete</a>", item.name));

    if(include_tr) {
        row += '</tr>';
    }

    return row;
}

$.fn.zato.config.runtime.delete_ = function(id) {
    $.fn.zato.data_table.delete_(id, 'td.item_id_',
        'Confif file `{0}` deleted',
        'Are you sure you want to delete the config file `{0}`?',
        true);
}
