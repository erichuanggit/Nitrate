Nitrate.Report.Builds = {}

Nitrate.Report.Builds.on_load = function()
{
		
		if($('report_build')) {
	        SortableTable.setup({
	            rowEvenClass : 'evenRow',
	            rowOddClass : 'oddRow',
	            nosortClass : 'nosort'
	        });

	        SortableTable.init('report_build');
	    }
		
}