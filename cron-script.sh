echo "Running weekly cron script for Datagetta project..."

echo "Running script to insert new data..."
docker exec python /bin/bash -c "cd /csvparser && python ftpPuller.py check_pull"

echo "Running script to format and clean data..."
docker exec postgres /bin/bash -c "psql -U dbgetta -d datagetta_db < /sql/team-assignment.sql"
docker exec postgres /bin/bash -c "psql -U dbgetta -d datagetta_db < /sql/keepd1.sql"

echo "Running python scripts to update models..."
docker exec python /bin/bash -c "cd /shifting_model && python main.py"
docker exec python /bin/bash -c "cd /SDProjectAIOrange && python updateheatmaps.py"