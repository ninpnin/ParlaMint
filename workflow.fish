# source workflow.fish ~/Work/riksdagen-corpus/corpus/protocols/201718/prot-201718--7.xml
conda_init && conda activate data
# test that conda works
python3 -c "import pandas as pd; print(pd)" 

#git checkout dev
echo $argv
git checkout dev

for f in $argv
    python3 Scripts/convert_rk.py --path $f
end

echo "Move to SE"
cd Data/ParlaMint-SE/
ll

echo "Run sparv..."
fish annotate.fish
echo "Clean annotations..."
python3 clean_annotations.py
echo "Count words..."
python3 count_words.py
echo "Generate metadata..."
python3 gen_metadata.py --metadata_db ~/Work/riksdagen-corpus/corpus/metadata/

echo "Move back to project root"
cd ../../
ll

git add Data/ParlaMint-SE/ParlaMint-SE.xml
git add Data/ParlaMint-SE/ParlaMint-SE.ana.xml
git checkout Data/ParlaMint-SE/ParlaMint-SE_*.xml
git add Data/ParlaMint-SE/ParlaMint-SE_*.xml

set paths (ls Data/ParlaMint-SE/ParlaMint-SE_*.xml)

git commit -m "chore: regenerate corpus files"

python3 Scripts/populate_links.py --path Data/ParlaMint-SE/ParlaMint-SE.ana.xml --out ParlaMint-SE.ana.xml
python3 Scripts/populate_links.py --path Data/ParlaMint-SE/ParlaMint-SE.xml --out ParlaMint-SE.xml

git checkout data

cp ParlaMint-SE.ana.xml Data/ParlaMint-SE/ParlaMint-SE.ana.xml
cp ParlaMint-SE.xml Data/ParlaMint-SE/ParlaMint-SE.xml

git add Data/ParlaMint-SE/ParlaMint-SE.xml
git add Data/ParlaMint-SE/ParlaMint-SE.ana.xml

echo $paths
for p in $paths
    git restore --source dev $p
end
git add Data/ParlaMint-SE/ParlaMint-SE_*.xml
git status

git commit -m "chore: copy files from 'dev'"
git push-all data