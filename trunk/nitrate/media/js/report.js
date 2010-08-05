Nitrate.Report = {}
Nitrate.Report.List = {}
Nitrate.Report.List.on_load = function(){
	$('coverage_search').observe('click', function(t) {
            var element = $('coverage_report_search');
            if(element.getStyle('display') == 'none'){
                element.show();
                this.update(default_messages.report.hide_search);
            } else {
                element.hide();
                this.update(default_messages.report.show_search);
            }
        })
	
	
	
	}

Nitrate.Report.Builds = {}

Nitrate.Report.Builds.on_load = function()
{
		
		if($('report_build')) {
	        TableKit.Sortable.init('report_build',
	        {
                rowEvenClass : 'roweven',
                rowOddClass : 'rowodd',
                nosortClass : 'nosort'
            });
	    }
		
}

