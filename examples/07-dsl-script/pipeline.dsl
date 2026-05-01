# Rebuild DSL Example Script
# This file demonstrates the DSL syntax for automating rebuild operations

# Walk command - analyze git history
walk repo:/home/tom/github/maskservice/c2004 days:7 deploy:docker-compose health_url:http://localhost:8101/api/v3/health base_url:http://localhost:8101 output:.rebuild_c2004_7d

# Analyze command - detect code duplicates
analyze repo:/home/tom/github/maskservice/c2004 type:duplicates min-lines:4

# Evolution command - generate timeline visualization
evolution timeline:.rebuild_c2004_7d/timeline.json output:evolution.html title:"C2004 Code Evolution"

# Auto-PR command - create pull request with analysis
auto-pr analysis:.rebuild_c2004_7d/duplication.json platform:github dry_run:true
