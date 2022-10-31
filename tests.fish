echo "RUN: val-schema"
make val-schema-SE 2> logs/val_schema.txt
echo "RUN: check-links"
make check-links-SE 2> logs/check_links.txt
echo "RUN: check-content"
make check-content-SE 2> logs/check_content.txt
echo "RUN: validate-parlamint"
make validate-parlamint-SE 2> logs/validate_parlamint.txt
echo "RUN: text"
make text-SE 2> logs/text.txt
echo "RUN: chars"
make chars-SE 2> logs/chars.txt
echo "RUN: meta"
make meta-SE 2> logs/meta.txt
echo "RUN: vertana"
make vertana-SE 2> logs/vertana.txt
echo "RUN: conllu"
make conllu-SE 2> logs/conllu.txt

echo "Print errors..."
touch all-errors.txt
for f in logs/*.txt
    set errorlog (sort $f | uniq | grep ERROR)
    echo $errorlog
    echo $errorlog >> all-errors.txt
end