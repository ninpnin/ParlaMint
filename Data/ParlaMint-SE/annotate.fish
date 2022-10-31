for f in ParlaMint-SE_*.xml;
    set ending (string sub --start=-7 $f);
    if [ "ana.xml" != $ending ]
        cp $f source
    end
end;

conda_init && conda activate data
#rm export/xml_export.pretty/*.xml
sparv run
rm source/*.xml