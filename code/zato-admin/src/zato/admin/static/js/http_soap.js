
// /////////////////////////////////////////////////////////////////////////////

$.fn.zato.data_table.HTTPSOAP = new Class({
    toString: function() {
        var s = '<HTTPSOAP id:{0} name:{1} is_active:{2}';
        return String.format(s, this.id ? this.id : '(none)',
                                this.name ? this.name : '(none)',
                                this.is_active ? this.is_active : '(none)');
    }
});

// /////////////////////////////////////////////////////////////////////////////

$(document).ready(function() {
    $('#data-table').tablesorter();
    $.fn.zato.data_table.class_ = $.fn.zato.data_table.HTTPSOAP;
    $.fn.zato.data_table.new_row_func = $.fn.zato.http_soap.data_table.new_row;
    $.fn.zato.data_table.parse();
    $.fn.zato.data_table.setup_forms(['name', 'url_path', 'service', 'security']);
})

$.fn.zato.http_soap.create = function() {
    $.fn.zato.data_table._create_edit('create', 'Create a new object', null);
}

$.fn.zato.http_soap.edit = function(id) {
    $.fn.zato.data_table._create_edit('edit', 'Update the object', id);
}

$.fn.zato.http_soap.data_table.new_row = function(item, data, include_tr) {
    var row = '';

    if(include_tr) {
        row += String.format("<tr id='tr_{0}' class='updated'>", item.id);
    }

    var is_active = item.is_active == true;

    var soap_action_tr = '';
    var soap_version_tr = '';
    var service_tr = '';

    if(data.transport == 'soap') {
        soap_action_tr += String.format('<td>{0}</td>', item.soap_action);
        soap_version_tr += String.format('<td>{0}</td>', item.soap_version);
    }
    
    if($(document).getUrlParam('connection') == 'channel') {
        var cluster_id = $(document).getUrlParam('cluster');
        service_tr += String.format('<td>{0}</td>', $.fn.zato.data_table.service_text(item.service, cluster_id));
    }
    
    row += "<td class='numbering'>&nbsp;</td>";
    row += "<td><input type='checkbox' /></td>";
    row += String.format('<td>{0}</td>', item.name);
    row += String.format('<td>{0}</td>', is_active ? 'Yes' : 'No');
    row += String.format('<td>{0}</td>', item.url_path);
    row += String.format('<td>{0}</td>', item.method);
    row += soap_action_tr;
    row += soap_version_tr;
    row += service_tr;
    row += String.format('<td>{0}</td>', item.security_select);
    row += String.format('<td>{0}</td>', String.format("<a href=\"javascript:$.fn.zato.http_soap.edit('{0}')\">Edit</a>", item.id));
    row += String.format('<td>{0}</td>', String.format("<a href='javascript:$.fn.zato.http_soap.delete_({0});'>Delete</a>", item.id));
    row += String.format("<td class='ignore item_id_{0}'>{0}</td>", item.id);
    row += String.format("<td class='ignore'>{0}</td>", is_active);

    if(include_tr) {
        row += '</tr>';
    }

    return row;
}

$.fn.zato.http_soap.delete_ = function(id) {
    $.fn.zato.data_table.delete_(id, 'td.item_id_',
        'Object [{0}] deleted',
        'Are you sure you want to delete the object [{0}]?',
        true);
}