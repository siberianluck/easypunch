$(document).ready(function(){
    $('.datepicker').pickadate({
        formatSubmit: 'yyyy-mm-dd'
    });
    $('.timepicker').timepicker({
        step: '15',
        scrollDefaultNow: true,
        timeFormat: 'H:i:s'
    });

    $('#forgot').click(function(){
        $('#dateOverride').show();
        $('.datepicker, .timepicker').removeAttr('disabled');
    });

    $('.employeeName, .accessCode').click(function(){
        var theChild = $(this).find('p')
        if (theChild.is("p")) {
            var theValue = theChild.html();
            console.log(theChild);
            $(this).html( "<input type='text' value='" + theValue + "' />");
        }
    });

    $('.employeeName, .accessCode').on("blur", "input", function(){
        //TODO save the value
        var theValue = $(this).val();
        var parentId = $(this).parent().attr('id');
        $(this).parent().html("<p>" + theValue + "</p>");

        console.log(parentId);

        var parentIdComponents = parentId.split("_");

        var parentType = parentIdComponents[0];
        var empId = parentIdComponents[1];

        data = {
            type: parentType,
            empId: empId,
            value: theValue
        }
        console.log('here');
        $.post('/update_emp', data, function(){
            alert('saved');
        })
    })
});
