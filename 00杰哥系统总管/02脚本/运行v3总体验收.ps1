# ============================================================
# Name: run-v3-acceptance.ps1
# Purpose: Run v3 manager acceptance checks in one command.
# Trigger: Manual execution after v3 preparation or construction work.
# Dependencies: PowerShell, Python, running v3 agent brain test service.
# Owner system: 00 system manager.
# Writes: Acceptance summary under 00 system manager log directory.
# Safety: Does not delete, overwrite, migrate, or stop production services.
# Change log: 2026-04-26 created first acceptance runner; fixed self-recursive script discovery; added workflow, n8n import review, message outlet, OpenClaw gateway, real dependency, evolution base verification, and tax real crawl readiness verification.
#             2026-04-27 paused tax construction by user request; acceptance runner now skips tax verification steps and adds WeWork assistant and content processing base verification.
#             2026-04-27 added low-risk gray access design verification for real-access pre-discussion stage.
#             2026-04-27 added old system protection verification to keep D:\杰哥智能体操作系统 independent and usable.
#             2026-04-27 added first batch n8n controlled-enable loop verification.
#             2026-04-27 added daily usable local entry verification.
#             2026-04-27 added daily task entry queue verification.
#             2026-04-27 added daily task confirmation verification.
#             2026-04-27 added daily task release-plan verification.
#             2026-04-27 added daily usable stage report verification.
#             2026-04-27 added stable hub heartbeat verification.
#             2026-04-27 added stable hub diagnosis-plan verification.
#             2026-04-27 added stable hub readonly patrol verification.
#             2026-04-27 added real-access master gate verification.
#             2026-04-27 added stock public readonly probe plan verification.
#             2026-04-27 added real assault candidate queue verification.
#             2026-04-27 added knowledge local ingest review verification.
#             2026-04-27 added office local draft gate verification.
#             2026-04-27 added video local material gate verification.
#             2026-04-27 added content local convert gate verification.
#             2026-04-27 added WeWork sandbox loop gate verification.
#             2026-04-27 added assault gate completion verification.
#             2026-04-27 added stock URL whitelist confirmation verification.
#             2026-04-27 added stock readonly request disabled-state verification.
#             2026-04-27 added knowledge write disabled-state verification.
#             2026-04-27 added office final output disabled-state verification.
#             2026-04-27 added video render disabled-state verification.
#             2026-04-27 added content real convert disabled-state verification.
#             2026-04-27 added WeWork real send disabled-state verification.
#             2026-04-27 added readonly disabled completion verification.
#             2026-04-27 added readonly execution plan verification.
#             2026-04-27 added readonly pre-execution snapshot verification.
#             2026-04-27 added readonly post-observation template verification.
#             2026-04-27 added readonly rollback template verification.
#             2026-04-27 added readonly observation loop verification.
#             2026-04-27 added readonly batch release form verification.
#             2026-04-27 added readonly execution design stage verification.
#             2026-04-27 added R01 stock readonly preflight verification.
#             2026-04-27 added R02 knowledge ingest preflight verification.
#             2026-04-27 added R03 office draft preflight verification.
#             2026-04-27 added first readonly batch preflight verification.
#             2026-04-27 added real readonly final gate verification.
#             2026-04-27 added current progress report verification.
#             2026-04-27 added real execution window register verification.
#             2026-04-27 added real execution permit order verification.
#             2026-04-27 added first batch dry-run record verification.
#             2026-04-27 added R01 stock readonly executor verification.
#             2026-04-27 added R02 knowledge local ingest executor verification.
#             2026-04-27 added R03 office draft executor verification.
#             2026-04-27 added first batch executor readiness table verification.
#             2026-04-27 added first batch scheduler adapter table verification.
#             2026-04-27 added first batch n8n disabled workflow draft verification.
#             2026-04-27 added daily usable assault status report verification.
#             2026-04-27 added model resource pool and manager decision core verification.
#             2026-04-27 added knowledge retrieval enhancement chain verification.
#             2026-04-27 added decision sample simulation verification.
#             2026-04-27 added unattended guardian permission tier verification.
#             2026-04-27 added unattended task state machine verification.
#             2026-04-27 added unattended task queue seed verification.
#             2026-04-28 added unattended task executor skeleton verification.
#             2026-04-28 added evolution sample cleanup gate verification.
#             2026-04-28 added human confirmation receipt state writeback draft verification.
#             2026-04-28 added unattended readonly patrol schedule draft verification.
#             2026-04-28 added unattended readonly patrol run record template verification.
#             2026-04-28 added unattended patrol failure diagnosis template verification.
#             2026-04-28 added patrol result experience candidate template verification.
#             2026-04-28 added unattended patrol user summary template verification.
#             2026-04-28 added stock daily research pipeline verification.
#             2026-04-28 added stock assistant independent experience verification.
#             2026-04-28 added stock old draft absorption verification.
#             2026-04-28 added stock layered filter blueprint verification.
#             2026-04-28 added stock review evolution loop verification.
#             2026-04-28 added stock review ledger runtime verification.
#             2026-04-28 added stock voice command tolerance verification.
#             2026-04-28 added stock voice clarification learning and technical indicator chain verification.
#             2026-04-28 added stock focus candidate pool verification.
#             2026-04-28 added stock L5 deep research report verification.
#             2026-04-28 added stock L5 review loop verification.
#             2026-04-28 added stock research status summary verification.
#             2026-04-28 added startup construction preflight verification.
#             2026-04-28 added construction handoff card verification.
#             2026-04-28 added stock daily usage package verification.
#             2026-04-28 added stock WeWork query dry-run verification.
#             2026-04-28 added stock WeWork query gray gate verification.
#             2026-04-28 added stock WeWork query n8n disabled draft verification.
#             2026-04-28 added stock WeWork message contract verification.
#             2026-04-28 added stock single instant report verification.
#             2026-04-28 added stock focus single report index verification.
#             2026-04-28 added stock WeWork single brief reply verification.
#             2026-04-28 added stock WeWork voice clarification reply verification.
#             2026-04-28 added stock WeWork voice confirmation learning reply verification.
#             2026-04-28 added stock WeWork unified message router dry-run verification.
#             2026-04-28 added stock WeWork n8n router contract verification.
#             2026-04-28 added stock WeWork n8n adapter dry-run verification.
#             2026-04-28 added stock WeWork n8n adapter workflow draft verification.
#             2026-04-28 added stock WeWork n8n import permit verification.
#             2026-04-28 added stock WeWork n8n inactive import plan verification.
#             2026-04-28 added concurrent latest-write race experience verification.
#             2026-04-28 added stock delivery gap list verification.
#             2026-04-28 added stock WeWork real-send credential isolation audit package verification.
#             2026-04-28 added stock WeWork real gray rollback plan package verification.
#             2026-04-28 added stock WeWork real gray whitelist trial package verification.
#             2026-04-28 added stock WeWork real gray human confirmation package verification.
#             2026-04-28 added stock WeWork real gray final preflight package verification.
#             2026-04-28 added stock WeWork real gray confirmation receipt package verification.
#             2026-04-28 added stock WeWork real gray unconfirmed guard package verification.
#             2026-04-28 added stock WeWork first real gray test record package verification.
#             2026-04-28 added stock assistant delivery readonly dashboard verification.
#             2026-04-28 added stock assistant delivery material index package verification.
#             2026-04-28 added stock assistant delivery remaining action package verification.
#             2026-04-28 added stock assistant delivery user summary package verification.
#             2026-04-28 added stock assistant delivery candidate package verification.
#             2026-04-28 added stock assistant delivery final selfcheck package verification.
#             2026-04-28 added stock assistant delivery submit package verification.
#             2026-04-28 added stock assistant real gray execution manual draft verification.
#             2026-04-28 added stock assistant real gray readonly environment snapshot verification.
#             2026-04-28 added stock assistant first real gray test message samples verification.
#             2026-04-28 added stock assistant first real gray test review template verification.
#             2026-04-28 added stock assistant real gray human release confirmation template verification.
#             2026-04-28 added stock assistant real gray final readonly release package verification.
#             2026-04-28 added stock assistant real gray user checklist verification.
#             2026-04-28 added stock assistant real gray high risk operation request template verification.
#             2026-04-28 added stock assistant n8n inactive import request verification.
#             2026-04-28 added stock assistant n8n inactive import preexecution readonly check verification.
#             2026-04-28 added stock assistant n8n inactive import human confirmation receipt template verification.
# ============================================================

[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"

$scriptDir = Split-Path -Parent $PSCommandPath
$managerDir = Split-Path -Parent $scriptDir
$root = Split-Path -Parent $managerDir
$logRoot = Get-ChildItem -Path $managerDir -Directory | Where-Object { $_.Name -like "04*" } | Select-Object -First 1
if (-not $logRoot) { throw "log root not found" }

$acceptDir = Join-Path $logRoot.FullName "acceptance"
New-Item -ItemType Directory -Force -Path $acceptDir | Out-Null
$reportPath = Join-Path $acceptDir "v3-acceptance-最新.json"

function Find-ScriptByMarker {
    param(
        [string]$Extension,
        [string]$Marker
    )
    Get-ChildItem -Path $scriptDir -File -Filter "*$Extension" |
        Where-Object { $_.FullName -ne $PSCommandPath } |
        Where-Object { (Get-Content -Path $_.FullName -Raw -ErrorAction SilentlyContinue) -like "*$Marker*" } |
        Select-Object -First 1
}

function Run-Step {
    param(
        [string]$Name,
        [string]$FilePath,
        [string]$Kind,
        [int]$TimeoutSec = 120
    )
    if (-not $FilePath) {
        return [pscustomobject]@{
            name = $Name
            ok = $false
            exit_code = 1
            output = @("script not found")
        }
    }

    $stdout = Join-Path $acceptDir "$Name-最新.out.log"
    $stderr = Join-Path $acceptDir "$Name-最新.err.log"
    if ($Kind -eq "powershell") {
        $exe = "powershell"
        $args = "-NoProfile -ExecutionPolicy Bypass -File `"$FilePath`""
    } else {
        $exe = "python"
        $args = "`"$FilePath`""
    }

    try {
        $proc = Start-Process -FilePath $exe -ArgumentList $args -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
        $finished = $proc.WaitForExit($TimeoutSec * 1000)
        if (-not $finished) {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            $exitCode = 124
            $output = @("timeout after $TimeoutSec seconds")
        } else {
            $proc.Refresh()
            $exitCode = $proc.ExitCode
            if ($null -eq $exitCode) { $exitCode = 0 }
            $output = @()
            if (Test-Path $stdout) { $output += Get-Content -Path $stdout -ErrorAction SilentlyContinue }
            if (Test-Path $stderr) { $output += Get-Content -Path $stderr -ErrorAction SilentlyContinue }
            $joinedOutput = ($output -join "`n")
            if ($joinedOutput -like "*Traceback*" -or $joinedOutput -like "*Exception in thread*" -or $joinedOutput -match '"失败"\s*:\s*[1-9]') {
                $exitCode = 1
            }
        }
    } catch {
        $output = @($_.Exception.Message)
        $exitCode = 1
    }
    [pscustomobject]@{
        name = $Name
        ok = ($exitCode -eq 0)
        exit_code = $exitCode
        output = ($output | ForEach-Object { "$_" })
    }
}

$prebuild = Find-ScriptByMarker ".ps1" "prebuild_check.ps1"
$readonly = Find-ScriptByMarker ".ps1" "read_only_status_check.ps1"
$annotation = Find-ScriptByMarker ".py" "annotation-check"
$realDependencyVerify = Find-ScriptByMarker ".py" "real-dependency-readonly-verify"
$agentVerify = Find-ScriptByMarker ".py" "agent-brain-verify"
$kbVerify = Find-ScriptByMarker ".py" "knowledge-base-verify"
$evolutionVerify = Find-ScriptByMarker ".py" "evolution-base-verify"
$workflowVerify = Find-ScriptByMarker ".py" "workflow-base-verify"
$n8nImportVerify = Find-ScriptByMarker ".py" "n8n-import-review-verify"
$lowRiskGrayVerify = Find-ScriptByMarker ".py" "low-risk-gray-access-verify"
$messageVerify = Find-ScriptByMarker ".py" "message-outlet-verify"
$openclawVerify = Find-ScriptByMarker ".py" "openclaw-gateway-verify"
$stockVerify = Find-ScriptByMarker ".py" "stock-base-verify"
$videoVerify = Find-ScriptByMarker ".py" "video-base-verify"
$workVerify = Find-ScriptByMarker ".py" "work-base-verify"
$contentVerify = Find-ScriptByMarker ".py" "content-processing-base-verify"
$weworkVerify = Find-ScriptByMarker ".py" "wework-assistant-base-verify"
$oldSystemProtectionVerify = Find-ScriptByMarker ".py" "old-system-protection-verify"
$firstBatchControlledVerify = Find-ScriptByMarker ".py" "first-batch-n8n-controlled-verify"
$dailyUsableEntryVerify = Find-ScriptByMarker ".py" "daily-usable-entry-verify"
$dailyTaskEntryQueueVerify = Find-ScriptByMarker ".py" "daily-task-entry-queue-verify"
$dailyTaskConfirmationVerify = Find-ScriptByMarker ".py" "daily-task-confirmation-verify"
$dailyTaskReleasePlanVerify = Find-ScriptByMarker ".py" "daily-task-release-plan-verify"
$dailyUsableStageReportVerify = Find-ScriptByMarker ".py" "daily-usable-stage-report-verify"
$stableHubHeartbeatVerify = Find-ScriptByMarker ".py" "stable-hub-heartbeat-verify"
$stableHubDiagnosisPlanVerify = Find-ScriptByMarker ".py" "stable-hub-diagnosis-plan-verify"
$stableHubPatrolVerify = Find-ScriptByMarker ".py" "stable-hub-patrol-verify"
$realAccessMasterGateVerify = Find-ScriptByMarker ".py" "real-access-master-gate-verify"
$stockPublicReadonlyProbeVerify = Find-ScriptByMarker ".py" "stock-public-readonly-probe-verify"
$realAssaultCandidateQueueVerify = Find-ScriptByMarker ".py" "real-assault-candidate-queue-verify"
$knowledgeLocalIngestReviewVerify = Find-ScriptByMarker ".py" "knowledge-local-ingest-review-verify"
$officeLocalDraftGateVerify = Find-ScriptByMarker ".py" "office-local-draft-gate-verify"
$videoLocalMaterialGateVerify = Find-ScriptByMarker ".py" "video-local-material-gate-verify"
$contentLocalConvertGateVerify = Find-ScriptByMarker ".py" "content-local-convert-gate-verify"
$weworkSandboxLoopGateVerify = Find-ScriptByMarker ".py" "wework-sandbox-loop-gate-verify"
$assaultGateCompletionVerify = Find-ScriptByMarker ".py" "assault-gate-completion-verify"
$stockUrlWhitelistConfirmationVerify = Find-ScriptByMarker ".py" "stock-url-whitelist-confirmation-verify"
$stockReadonlyRequestDisabledVerify = Find-ScriptByMarker ".py" "stock-readonly-request-disabled-verify"
$knowledgeWriteDisabledVerify = Find-ScriptByMarker ".py" "knowledge-write-disabled-verify"
$officeFinalOutputDisabledVerify = Find-ScriptByMarker ".py" "office-final-output-disabled-verify"
$videoRenderDisabledVerify = Find-ScriptByMarker ".py" "video-render-disabled-verify"
$contentRealConvertDisabledVerify = Find-ScriptByMarker ".py" "content-real-convert-disabled-verify"
$weworkRealSendDisabledVerify = Find-ScriptByMarker ".py" "wework-real-send-disabled-verify"
$readonlyDisabledCompletionVerify = Find-ScriptByMarker ".py" "readonly-disabled-completion-verify"
$readonlyExecutionPlanVerify = Find-ScriptByMarker ".py" "readonly-execution-plan-verify"
$readonlyPreExecutionSnapshotVerify = Find-ScriptByMarker ".py" "readonly-pre-execution-snapshot-verify"
$readonlyPostObservationTemplateVerify = Find-ScriptByMarker ".py" "readonly-post-observation-template-verify"
$readonlyRollbackTemplateVerify = Find-ScriptByMarker ".py" "readonly-rollback-template-verify"
$readonlyObservationLoopVerify = Find-ScriptByMarker ".py" "readonly-observation-loop-verify"
$readonlyBatchReleaseFormVerify = Find-ScriptByMarker ".py" "readonly-batch-release-form-verify"
$readonlyExecutionDesignStageVerify = Find-ScriptByMarker ".py" "readonly-execution-design-stage-verify"
$r01StockReadonlyPreflightVerify = Find-ScriptByMarker ".py" "r01-stock-readonly-preflight-verify"
$r02KnowledgeIngestPreflightVerify = Find-ScriptByMarker ".py" "r02-knowledge-ingest-preflight-verify"
$r03OfficeDraftPreflightVerify = Find-ScriptByMarker ".py" "r03-office-draft-preflight-verify"
$firstReadonlyBatchPreflightVerify = Find-ScriptByMarker ".py" "first-readonly-batch-preflight-verify"
$realReadonlyFinalGateVerify = Find-ScriptByMarker ".py" "real-readonly-final-gate-verify"
$currentProgressReportVerify = Find-ScriptByMarker ".py" "current-progress-report-verify"
$realExecutionWindowRegisterVerify = Find-ScriptByMarker ".py" "real-execution-window-register-verify"
$realExecutionPermitOrderVerify = Find-ScriptByMarker ".py" "real-execution-permit-order-verify"
$firstBatchDryRunRecordVerify = Find-ScriptByMarker ".py" "first-batch-dry-run-record-verify"
$r01StockReadonlyExecutorVerify = Find-ScriptByMarker ".py" "r01-stock-readonly-executor-verify"
$r02KnowledgeLocalIngestExecutorVerify = Find-ScriptByMarker ".py" "r02-knowledge-local-ingest-executor-verify"
$r03OfficeDraftExecutorVerify = Find-ScriptByMarker ".py" "r03-office-draft-executor-verify"
$firstBatchExecutorReadinessTableVerify = Find-ScriptByMarker ".py" "first-batch-executor-readiness-table-verify"
$firstBatchSchedulerAdapterTableVerify = Find-ScriptByMarker ".py" "first-batch-scheduler-adapter-table-verify"
$firstBatchN8nDisabledWorkflowDraftVerify = Find-ScriptByMarker ".py" "first-batch-n8n-disabled-workflow-draft-verify"
$dailyUsableAssaultStatusReportVerify = Find-ScriptByMarker ".py" "daily-usable-assault-status-report-verify"
$modelResourcePoolRegisterVerify = Find-ScriptByMarker ".py" "model-resource-pool-register-verify"
$managerDecisionCoreRegisterVerify = Find-ScriptByMarker ".py" "manager-decision-core-register-verify"
$knowledgeRetrievalEnhancementChainVerify = Find-ScriptByMarker ".py" "knowledge-retrieval-enhancement-chain-verify"
$decisionSampleSimulationVerify = Find-ScriptByMarker ".py" "decision-sample-simulation-verify"
$unattendedGuardianPermissionTierVerify = Find-ScriptByMarker ".py" "unattended-guardian-permission-tier-verify"
$unattendedTaskStateMachineVerify = Find-ScriptByMarker ".py" "unattended-task-state-machine-verify"
$unattendedTaskQueueSeedVerify = Find-ScriptByMarker ".py" "unattended-task-queue-seed-verify"
$unattendedTaskExecutorSkeletonVerify = Find-ScriptByMarker ".py" "unattended-task-executor-skeleton-verify"
$evolutionSampleCleanupGateVerify = Find-ScriptByMarker ".py" "evolution-sample-cleanup-gate-verify"
$humanConfirmationReceiptWritebackVerify = Find-ScriptByMarker ".py" "human-confirmation-receipt-state-writeback-draft-verify"
$unattendedReadonlyPatrolScheduleDraftVerify = Find-ScriptByMarker ".py" "unattended-readonly-patrol-schedule-draft-verify"
$unattendedReadonlyPatrolRunRecordTemplateVerify = Find-ScriptByMarker ".py" "unattended-readonly-patrol-run-record-template-verify"
$unattendedPatrolFailureDiagnosisTemplateVerify = Find-ScriptByMarker ".py" "unattended-patrol-failure-diagnosis-template-verify"
$patrolResultExperienceCandidateTemplateVerify = Find-ScriptByMarker ".py" "patrol-result-experience-candidate-template-verify"
$unattendedPatrolUserSummaryTemplateVerify = Find-ScriptByMarker ".py" "unattended-patrol-user-summary-template-verify"
$stockDailyResearchPipelineVerify = Find-ScriptByMarker ".py" "stock-daily-research-pipeline-verify"
$stockAssistantExperienceSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-experience-summary-verify"
$stockDraftAbsorptionSummaryVerify = Find-ScriptByMarker ".py" "stock-draft-absorption-summary-verify"
$stockLayeredFilterBlueprintSummaryVerify = Find-ScriptByMarker ".py" "stock-layered-filter-blueprint-summary-verify"
$stockReviewEvolutionLoopSummaryVerify = Find-ScriptByMarker ".py" "stock-review-evolution-loop-summary-verify"
$stockReviewLedgerRuntimeSummaryVerify = Find-ScriptByMarker ".py" "stock-review-ledger-runtime-summary-verify"
$stockVoiceCommandToleranceSummaryVerify = Find-ScriptByMarker ".py" "stock-voice-command-tolerance-summary-verify"
$stockVoiceClarificationLearningSummaryVerify = Find-ScriptByMarker ".py" "stock-voice-clarification-learning-summary-verify"
$stockTechnicalIndicatorChainSummaryVerify = Find-ScriptByMarker ".py" "stock-technical-indicator-chain-summary-verify"
$stockFocusCandidatePoolSummaryVerify = Find-ScriptByMarker ".py" "stock-focus-candidate-pool-summary-verify"
$stockL5DeepResearchReportSummaryVerify = Find-ScriptByMarker ".py" "stock-l5-deep-research-report-summary-verify"
$stockL5ReviewLoopSummaryVerify = Find-ScriptByMarker ".py" "stock-l5-review-loop-summary-verify"
$stockResearchStatusSummaryVerify = Find-ScriptByMarker ".py" "stock-research-status-summary-verify"
$startupConstructionPreflightVerify = Find-ScriptByMarker ".py" "startup-construction-preflight-verify"
$constructionHandoffCardVerify = Find-ScriptByMarker ".py" "construction-handoff-card-verify"
$stockDailyUsagePackageSummaryVerify = Find-ScriptByMarker ".py" "stock-daily-usage-package-summary-verify"
$stockWeworkQueryDryrunSummaryVerify = Find-ScriptByMarker ".py" "stock-wework-query-dryrun-summary-verify"
$stockWeworkQueryGrayGateSummaryVerify = Find-ScriptByMarker ".py" "stock-wework-query-gray-gate-summary-verify"
$stockWeworkQueryN8nDisabledDraftSummaryVerify = Find-ScriptByMarker ".py" "stock-wework-query-n8n-disabled-draft-summary-verify"
$stockWeworkMessageContractSummaryVerify = Find-ScriptByMarker ".py" "stock-wework-message-contract-summary-verify"
$stockSingleInstantReportSummaryVerify = Find-ScriptByMarker ".py" "stock-single-instant-report-summary-verify"
$stockFocusSingleReportIndexSummaryVerify = Find-ScriptByMarker ".py" "stock-focus-single-report-index-summary-verify"
$stockWeworkSingleBriefReplySummaryVerify = Find-ScriptByMarker ".py" "stock-wework-single-brief-reply-summary-verify"
$stockWeworkVoiceClarificationReplySummaryVerify = Find-ScriptByMarker ".py" "stock-wework-voice-clarification-reply-summary-verify"
$stockWeworkVoiceConfirmLearningReplySummaryVerify = Find-ScriptByMarker ".py" "stock-wework-voice-confirm-learning-reply-summary-verify"
$stockWeworkMessageRouterDryrunSummaryVerify = Find-ScriptByMarker ".py" "stock-wework-message-router-dryrun-summary-verify"
$stockWeworkN8nRouterContractSummaryVerify = Find-ScriptByMarker ".py" "stock-wework-n8n-router-contract-summary-verify"
$stockWeworkN8nAdapterDryrunSummaryVerify = Find-ScriptByMarker ".py" "stock-wework-n8n-adapter-dryrun-summary-verify"
$stockWeworkN8nAdapterWorkflowDraftSummaryVerify = Find-ScriptByMarker ".py" "stock-wework-n8n-adapter-workflow-draft-summary-verify"
$stockWeworkN8nImportPermitSummaryVerify = Find-ScriptByMarker ".py" "stock-wework-n8n-import-permit-summary-verify"
$stockWeworkN8nInactiveImportPlanSummaryVerify = Find-ScriptByMarker ".py" "stock-wework-n8n-inactive-import-plan-summary-verify"
$concurrentLatestWriteExperienceSummaryVerify = Find-ScriptByMarker ".py" "evolution-concurrent-latest-write-experience-summary-verify"
$stockDeliveryGapListSummaryVerify = Find-ScriptByMarker ".py" "stock-delivery-gap-list-summary-verify"
$stockAfterHoursBatchResourcePlanSummaryVerify = Find-ScriptByMarker ".py" "stock-after-hours-batch-resource-plan-summary-verify"
$stockOpenClawMessageBridgeContractSummaryVerify = Find-ScriptByMarker ".py" "stock-openclaw-message-bridge-contract-summary-verify"
$stockUnifiedMessageOutletDisabledPackageSummaryVerify = Find-ScriptByMarker ".py" "stock-unified-message-outlet-disabled-package-summary-verify"
$stockDeliveryAcceptanceChecklistSummaryVerify = Find-ScriptByMarker ".py" "stock-delivery-acceptance-checklist-summary-verify"
$stockWeworkRealGrayFinalGatePackageSummaryVerify = Find-ScriptByMarker ".py" "stock-wework-real-gray-final-gate-package-summary-verify"
$stockAssistantPrereFreshReadonlyStatusCheckSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-prerefresh-readonly-status-check-summary-verify"
$stockN8nInactiveImportPrereadAuditPackageSummaryVerify = Find-ScriptByMarker ".py" "stock-n8n-inactive-import-preread-audit-package-summary-verify"
$stockOpenClawBridgeSandboxAcceptancePackageSummaryVerify = Find-ScriptByMarker ".py" "stock-openclaw-bridge-sandbox-acceptance-package-summary-verify"
$stockWeworkRealSendCredentialIsolationAuditPackageSummaryVerify = Find-ScriptByMarker ".py" "stock-wework-real-send-credential-isolation-audit-package-summary-verify"
$stockWeworkRealGrayRollbackPlanPackageSummaryVerify = Find-ScriptByMarker ".py" "stock-wework-real-gray-rollback-plan-package-summary-verify"
$stockWeworkRealGrayWhitelistTrialPackageSummaryVerify = Find-ScriptByMarker ".py" "stock-wework-real-gray-whitelist-trial-package-summary-verify"
$stockWeworkRealGrayHumanConfirmationPackageSummaryVerify = Find-ScriptByMarker ".py" "stock-wework-real-gray-human-confirmation-package-summary-verify"
$stockWeworkRealGrayFinalPreflightPackageSummaryVerify = Find-ScriptByMarker ".py" "stock-wework-real-gray-final-preflight-package-summary-verify"
$stockWeworkRealGrayConfirmationReceiptPackageSummaryVerify = Find-ScriptByMarker ".py" "stock-wework-real-gray-confirmation-receipt-package-summary-verify"
$stockWeworkRealGrayUnconfirmedGuardPackageSummaryVerify = Find-ScriptByMarker ".py" "stock-wework-real-gray-unconfirmed-guard-package-summary-verify"
$stockWeworkFirstRealGrayTestRecordPackageSummaryVerify = Find-ScriptByMarker ".py" "stock-wework-first-real-gray-test-record-package-summary-verify"
$stockAssistantDeliveryReadonlyDashboardSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-delivery-readonly-dashboard-summary-verify"
$stockAssistantDeliveryMaterialIndexPackageSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-delivery-material-index-package-summary-verify"
$stockAssistantDeliveryRemainingActionPackageSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-delivery-remaining-action-package-summary-verify"
$stockAssistantDeliveryUserSummaryPackageSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-delivery-user-summary-package-summary-verify"
$stockAssistantDeliveryCandidatePackageSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-delivery-candidate-package-summary-verify"
$stockAssistantDeliveryFinalSelfcheckPackageSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-delivery-final-selfcheck-package-summary-verify"
$stockAssistantDeliverySubmitPackageSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-delivery-submit-package-summary-verify"
$stockAssistantRealGrayExecutionManualDraftSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-real-gray-execution-manual-draft-summary-verify"
$stockAssistantRealGrayReadonlyEnvironmentSnapshotSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-real-gray-readonly-environment-snapshot-summary-verify"
$stockAssistantFirstRealGrayTestMessageSamplesSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-first-real-gray-test-message-samples-summary-verify"
$stockAssistantFirstRealGrayTestReviewTemplateSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-first-real-gray-test-review-template-summary-verify"
$stockAssistantRealGrayHumanReleaseConfirmationTemplateSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-real-gray-human-release-confirmation-template-summary-verify"
$stockAssistantRealGrayFinalReadonlyReleasePackageSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-real-gray-final-readonly-release-package-summary-verify"
$stockAssistantRealGrayUserChecklistSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-real-gray-user-checklist-summary-verify"
$stockAssistantRealGrayHighRiskOperationRequestTemplateSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-real-gray-high-risk-operation-request-template-summary-verify"
$stockAssistantN8nInactiveImportRequestSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-n8n-inactive-import-request-summary-verify"
$stockAssistantN8nInactiveImportPreexecutionReadonlyCheckSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-n8n-inactive-import-preexecution-readonly-check-summary-verify"
$stockAssistantN8nInactiveImportHumanConfirmationReceiptTemplateSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-n8n-inactive-import-human-confirmation-receipt-template-summary-verify"
$stockAssistantN8nTargetIsolationPackageVerify = Find-ScriptByMarker ".py" "stock-assistant-n8n-target-isolation-package-verify"
$stockAssistantIsolatedN8nImplementationRequestSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-isolated-n8n-implementation-request-summary-verify"
$stockAssistantIsolatedN8nStartupPreflightSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-isolated-n8n-startup-preflight-summary-verify"
$isolatedN8nControlledStartConfigSummaryVerify = Find-ScriptByMarker ".py" "isolated-n8n-controlled-start-config-summary-verify"
$stockAssistantN8nInactiveImportResultSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-n8n-inactive-import-result-summary-verify"
$stockAssistantGrayConnectivityPreflightSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-gray-connectivity-preflight-summary-verify"
$stockAssistantLocalGrayConnectivityDrillSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-local-gray-connectivity-drill-summary-verify"
$stockAssistantRealWeworkGrayGapListSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-real-wework-gray-gap-list-summary-verify"
$stockAssistantWeworkControlledSendGatePackageSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-wework-controlled-send-gate-package-summary-verify"
$stockAssistantN8nWebhookGrayEntryArtifactSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-n8n-webhook-gray-entry-artifact-summary-verify"
$stockAssistantN8nWebhookGrayEntryInactiveImportResultSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-n8n-webhook-gray-entry-inactive-import-result-summary-verify"
$stockAssistantN8nWebhookLocalControlledEnableTestSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-n8n-webhook-local-controlled-enable-test-summary-verify"
$stockAssistantN8nLocalExecutionLoopTestSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-n8n-local-execution-loop-test-summary-verify"
$stockAssistantN8nControlledRefreshRestartRequestPackageSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-n8n-controlled-refresh-restart-request-package-summary-verify"
$stockAssistantN8nControlledRefreshRestartPreexecutionSnapshotSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-n8n-controlled-refresh-restart-preexecution-snapshot-summary-verify"
$stockAssistantN8nPostRefreshWebhookGrayAcceptancePlanSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-n8n-post-refresh-webhook-gray-acceptance-plan-summary-verify"
$stockAssistantDeliveryUsagePackageSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-delivery-usage-package-summary-verify"
$stockAssistantDeliveryRuntimePatrolPackageSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-delivery-runtime-patrol-package-summary-verify"
$stockAssistantLocalDeliveryFunctionalAcceptancePackageSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-local-delivery-functional-acceptance-package-summary-verify"
$stockAssistantLocalServiceRefreshRequestPackageSummaryVerify = Find-ScriptByMarker ".py" "stock-assistant-local-service-refresh-request-package-summary-verify"

$steps = @()
$steps += Run-Step "prebuild_check" $prebuild.FullName "powershell" 60
$steps += Run-Step "annotation_check" $annotation.FullName "python" 60
$steps += Run-Step "read_only_status_check" $readonly.FullName "powershell" 120
$steps += Run-Step "real_dependency_readonly_verify" $realDependencyVerify.FullName "python" 120
$steps += Run-Step "agent_brain_verify" $agentVerify.FullName "python" 300
$steps += Run-Step "knowledge_base_verify" $kbVerify.FullName "python" 120
$steps += Run-Step "evolution_base_verify" $evolutionVerify.FullName "python" 120
$steps += Run-Step "workflow_base_verify" $workflowVerify.FullName "python" 120
$steps += Run-Step "n8n_import_review_verify" $n8nImportVerify.FullName "python" 120
$steps += Run-Step "low_risk_gray_access_verify" $lowRiskGrayVerify.FullName "python" 120
$steps += Run-Step "message_outlet_verify" $messageVerify.FullName "python" 120
$steps += Run-Step "openclaw_gateway_verify" $openclawVerify.FullName "python" 120
$steps += Run-Step "stock_base_verify" $stockVerify.FullName "python" 120
$steps += Run-Step "video_base_verify" $videoVerify.FullName "python" 120
$steps += Run-Step "work_base_verify" $workVerify.FullName "python" 120
$steps += Run-Step "content_processing_base_verify" $contentVerify.FullName "python" 120
$steps += Run-Step "wework_assistant_base_verify" $weworkVerify.FullName "python" 120
$steps += Run-Step "old_system_protection_verify" $oldSystemProtectionVerify.FullName "python" 120
$steps += Run-Step "first_batch_n8n_controlled_verify" $firstBatchControlledVerify.FullName "python" 120
$steps += Run-Step "daily_usable_entry_verify" $dailyUsableEntryVerify.FullName "python" 180
$steps += Run-Step "daily_task_entry_queue_verify" $dailyTaskEntryQueueVerify.FullName "python" 180
$steps += Run-Step "daily_task_confirmation_verify" $dailyTaskConfirmationVerify.FullName "python" 180
$steps += Run-Step "daily_task_release_plan_verify" $dailyTaskReleasePlanVerify.FullName "python" 180
$steps += Run-Step "daily_usable_stage_report_verify" $dailyUsableStageReportVerify.FullName "python" 180
$steps += Run-Step "stable_hub_heartbeat_verify" $stableHubHeartbeatVerify.FullName "python" 180
$steps += Run-Step "stable_hub_diagnosis_plan_verify" $stableHubDiagnosisPlanVerify.FullName "python" 180
$steps += Run-Step "stable_hub_patrol_verify" $stableHubPatrolVerify.FullName "python" 240
$steps += Run-Step "real_access_master_gate_verify" $realAccessMasterGateVerify.FullName "python" 240
$steps += Run-Step "stock_public_readonly_probe_verify" $stockPublicReadonlyProbeVerify.FullName "python" 180
$steps += Run-Step "real_assault_candidate_queue_verify" $realAssaultCandidateQueueVerify.FullName "python" 180
$steps += Run-Step "knowledge_local_ingest_review_verify" $knowledgeLocalIngestReviewVerify.FullName "python" 180
$steps += Run-Step "office_local_draft_gate_verify" $officeLocalDraftGateVerify.FullName "python" 180
$steps += Run-Step "video_local_material_gate_verify" $videoLocalMaterialGateVerify.FullName "python" 180
$steps += Run-Step "content_local_convert_gate_verify" $contentLocalConvertGateVerify.FullName "python" 180
$steps += Run-Step "wework_sandbox_loop_gate_verify" $weworkSandboxLoopGateVerify.FullName "python" 180
$steps += Run-Step "assault_gate_completion_verify" $assaultGateCompletionVerify.FullName "python" 180
$steps += Run-Step "stock_url_whitelist_confirmation_verify" $stockUrlWhitelistConfirmationVerify.FullName "python" 180
$steps += Run-Step "stock_readonly_request_disabled_verify" $stockReadonlyRequestDisabledVerify.FullName "python" 180
$steps += Run-Step "knowledge_write_disabled_verify" $knowledgeWriteDisabledVerify.FullName "python" 180
$steps += Run-Step "office_final_output_disabled_verify" $officeFinalOutputDisabledVerify.FullName "python" 180
$steps += Run-Step "video_render_disabled_verify" $videoRenderDisabledVerify.FullName "python" 180
$steps += Run-Step "content_real_convert_disabled_verify" $contentRealConvertDisabledVerify.FullName "python" 180
$steps += Run-Step "wework_real_send_disabled_verify" $weworkRealSendDisabledVerify.FullName "python" 180
$steps += Run-Step "readonly_disabled_completion_verify" $readonlyDisabledCompletionVerify.FullName "python" 180
$steps += Run-Step "readonly_execution_plan_verify" $readonlyExecutionPlanVerify.FullName "python" 180
$steps += Run-Step "readonly_pre_execution_snapshot_verify" $readonlyPreExecutionSnapshotVerify.FullName "python" 180
$steps += Run-Step "readonly_post_observation_template_verify" $readonlyPostObservationTemplateVerify.FullName "python" 180
$steps += Run-Step "readonly_rollback_template_verify" $readonlyRollbackTemplateVerify.FullName "python" 180
$steps += Run-Step "readonly_observation_loop_verify" $readonlyObservationLoopVerify.FullName "python" 180
$steps += Run-Step "readonly_batch_release_form_verify" $readonlyBatchReleaseFormVerify.FullName "python" 180
$steps += Run-Step "readonly_execution_design_stage_verify" $readonlyExecutionDesignStageVerify.FullName "python" 180
$steps += Run-Step "r01_stock_readonly_preflight_verify" $r01StockReadonlyPreflightVerify.FullName "python" 180
$steps += Run-Step "r02_knowledge_ingest_preflight_verify" $r02KnowledgeIngestPreflightVerify.FullName "python" 180
$steps += Run-Step "r03_office_draft_preflight_verify" $r03OfficeDraftPreflightVerify.FullName "python" 180
$steps += Run-Step "first_readonly_batch_preflight_verify" $firstReadonlyBatchPreflightVerify.FullName "python" 180
$steps += Run-Step "real_readonly_final_gate_verify" $realReadonlyFinalGateVerify.FullName "python" 180
$steps += Run-Step "current_progress_report_verify" $currentProgressReportVerify.FullName "python" 180
$steps += Run-Step "real_execution_window_register_verify" $realExecutionWindowRegisterVerify.FullName "python" 180
$steps += Run-Step "real_execution_permit_order_verify" $realExecutionPermitOrderVerify.FullName "python" 180
$steps += Run-Step "first_batch_dry_run_record_verify" $firstBatchDryRunRecordVerify.FullName "python" 180
$steps += Run-Step "r01_stock_readonly_executor_verify" $r01StockReadonlyExecutorVerify.FullName "python" 180
$steps += Run-Step "r02_knowledge_local_ingest_executor_verify" $r02KnowledgeLocalIngestExecutorVerify.FullName "python" 180
$steps += Run-Step "r03_office_draft_executor_verify" $r03OfficeDraftExecutorVerify.FullName "python" 180
$steps += Run-Step "first_batch_executor_readiness_table_verify" $firstBatchExecutorReadinessTableVerify.FullName "python" 180
$steps += Run-Step "first_batch_scheduler_adapter_table_verify" $firstBatchSchedulerAdapterTableVerify.FullName "python" 180
$steps += Run-Step "first_batch_n8n_disabled_workflow_draft_verify" $firstBatchN8nDisabledWorkflowDraftVerify.FullName "python" 180
$steps += Run-Step "daily_usable_assault_status_report_verify" $dailyUsableAssaultStatusReportVerify.FullName "python" 180
$steps += Run-Step "model_resource_pool_register_verify" $modelResourcePoolRegisterVerify.FullName "python" 180
$steps += Run-Step "manager_decision_core_register_verify" $managerDecisionCoreRegisterVerify.FullName "python" 180
$steps += Run-Step "knowledge_retrieval_enhancement_chain_verify" $knowledgeRetrievalEnhancementChainVerify.FullName "python" 180
$steps += Run-Step "decision_sample_simulation_verify" $decisionSampleSimulationVerify.FullName "python" 180
$steps += Run-Step "unattended_guardian_permission_tier_verify" $unattendedGuardianPermissionTierVerify.FullName "python" 180
$steps += Run-Step "unattended_task_state_machine_verify" $unattendedTaskStateMachineVerify.FullName "python" 180
$steps += Run-Step "unattended_task_queue_seed_verify" $unattendedTaskQueueSeedVerify.FullName "python" 180
$steps += Run-Step "unattended_task_executor_skeleton_verify" $unattendedTaskExecutorSkeletonVerify.FullName "python" 180
$steps += Run-Step "evolution_sample_cleanup_gate_verify" $evolutionSampleCleanupGateVerify.FullName "python" 180
$steps += Run-Step "human_confirmation_receipt_writeback_verify" $humanConfirmationReceiptWritebackVerify.FullName "python" 180
$steps += Run-Step "unattended_readonly_patrol_schedule_draft_verify" $unattendedReadonlyPatrolScheduleDraftVerify.FullName "python" 180
$steps += Run-Step "unattended_readonly_patrol_run_record_template_verify" $unattendedReadonlyPatrolRunRecordTemplateVerify.FullName "python" 180
$steps += Run-Step "unattended_patrol_failure_diagnosis_template_verify" $unattendedPatrolFailureDiagnosisTemplateVerify.FullName "python" 180
$steps += Run-Step "patrol_result_experience_candidate_template_verify" $patrolResultExperienceCandidateTemplateVerify.FullName "python" 180
$steps += Run-Step "unattended_patrol_user_summary_template_verify" $unattendedPatrolUserSummaryTemplateVerify.FullName "python" 180
$steps += Run-Step "stock_daily_research_pipeline_verify" $stockDailyResearchPipelineVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_experience_summary_verify" $stockAssistantExperienceSummaryVerify.FullName "python" 240
$steps += Run-Step "stock_draft_absorption_summary_verify" $stockDraftAbsorptionSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_layered_filter_blueprint_summary_verify" $stockLayeredFilterBlueprintSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_review_evolution_loop_summary_verify" $stockReviewEvolutionLoopSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_review_ledger_runtime_summary_verify" $stockReviewLedgerRuntimeSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_voice_command_tolerance_summary_verify" $stockVoiceCommandToleranceSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_voice_clarification_learning_summary_verify" $stockVoiceClarificationLearningSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_technical_indicator_chain_summary_verify" $stockTechnicalIndicatorChainSummaryVerify.FullName "python" 300
$steps += Run-Step "stock_focus_candidate_pool_summary_verify" $stockFocusCandidatePoolSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_l5_deep_research_report_summary_verify" $stockL5DeepResearchReportSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_l5_review_loop_summary_verify" $stockL5ReviewLoopSummaryVerify.FullName "python" 300
$steps += Run-Step "stock_research_status_summary_verify" $stockResearchStatusSummaryVerify.FullName "python" 180
$steps += Run-Step "startup_construction_preflight_verify" $startupConstructionPreflightVerify.FullName "python" 180
$steps += Run-Step "construction_handoff_card_verify" $constructionHandoffCardVerify.FullName "python" 180
$steps += Run-Step "stock_daily_usage_package_summary_verify" $stockDailyUsagePackageSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_wework_query_dryrun_summary_verify" $stockWeworkQueryDryrunSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_wework_query_gray_gate_summary_verify" $stockWeworkQueryGrayGateSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_wework_query_n8n_disabled_draft_summary_verify" $stockWeworkQueryN8nDisabledDraftSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_wework_message_contract_summary_verify" $stockWeworkMessageContractSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_single_instant_report_summary_verify" $stockSingleInstantReportSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_focus_single_report_index_summary_verify" $stockFocusSingleReportIndexSummaryVerify.FullName "python" 240
$steps += Run-Step "stock_wework_single_brief_reply_summary_verify" $stockWeworkSingleBriefReplySummaryVerify.FullName "python" 180
$steps += Run-Step "stock_wework_voice_clarification_reply_summary_verify" $stockWeworkVoiceClarificationReplySummaryVerify.FullName "python" 180
$steps += Run-Step "stock_wework_voice_confirm_learning_reply_summary_verify" $stockWeworkVoiceConfirmLearningReplySummaryVerify.FullName "python" 180
$steps += Run-Step "stock_wework_message_router_dryrun_summary_verify" $stockWeworkMessageRouterDryrunSummaryVerify.FullName "python" 240
$steps += Run-Step "stock_wework_n8n_router_contract_summary_verify" $stockWeworkN8nRouterContractSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_wework_n8n_adapter_dryrun_summary_verify" $stockWeworkN8nAdapterDryrunSummaryVerify.FullName "python" 300
$steps += Run-Step "stock_wework_n8n_adapter_workflow_draft_summary_verify" $stockWeworkN8nAdapterWorkflowDraftSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_wework_n8n_import_permit_summary_verify" $stockWeworkN8nImportPermitSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_wework_n8n_inactive_import_plan_summary_verify" $stockWeworkN8nInactiveImportPlanSummaryVerify.FullName "python" 180
$steps += Run-Step "concurrent_latest_write_experience_summary_verify" $concurrentLatestWriteExperienceSummaryVerify.FullName "python" 120
$steps += Run-Step "stock_delivery_gap_list_summary_verify" $stockDeliveryGapListSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_after_hours_batch_resource_plan_summary_verify" $stockAfterHoursBatchResourcePlanSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_openclaw_message_bridge_contract_summary_verify" $stockOpenClawMessageBridgeContractSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_unified_message_outlet_disabled_package_summary_verify" $stockUnifiedMessageOutletDisabledPackageSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_delivery_acceptance_checklist_summary_verify" $stockDeliveryAcceptanceChecklistSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_wework_real_gray_final_gate_package_summary_verify" $stockWeworkRealGrayFinalGatePackageSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_prerefresh_readonly_status_check_summary_verify" $stockAssistantPrereFreshReadonlyStatusCheckSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_n8n_inactive_import_preread_audit_package_summary_verify" $stockN8nInactiveImportPrereadAuditPackageSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_openclaw_bridge_sandbox_acceptance_package_summary_verify" $stockOpenClawBridgeSandboxAcceptancePackageSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_wework_real_send_credential_isolation_audit_package_summary_verify" $stockWeworkRealSendCredentialIsolationAuditPackageSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_wework_real_gray_rollback_plan_package_summary_verify" $stockWeworkRealGrayRollbackPlanPackageSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_wework_real_gray_whitelist_trial_package_summary_verify" $stockWeworkRealGrayWhitelistTrialPackageSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_wework_real_gray_human_confirmation_package_summary_verify" $stockWeworkRealGrayHumanConfirmationPackageSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_wework_real_gray_final_preflight_package_summary_verify" $stockWeworkRealGrayFinalPreflightPackageSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_wework_real_gray_confirmation_receipt_package_summary_verify" $stockWeworkRealGrayConfirmationReceiptPackageSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_wework_real_gray_unconfirmed_guard_package_summary_verify" $stockWeworkRealGrayUnconfirmedGuardPackageSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_wework_first_real_gray_test_record_package_summary_verify" $stockWeworkFirstRealGrayTestRecordPackageSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_delivery_readonly_dashboard_summary_verify" $stockAssistantDeliveryReadonlyDashboardSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_delivery_material_index_package_summary_verify" $stockAssistantDeliveryMaterialIndexPackageSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_delivery_remaining_action_package_summary_verify" $stockAssistantDeliveryRemainingActionPackageSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_delivery_user_summary_package_summary_verify" $stockAssistantDeliveryUserSummaryPackageSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_delivery_candidate_package_summary_verify" $stockAssistantDeliveryCandidatePackageSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_delivery_final_selfcheck_package_summary_verify" $stockAssistantDeliveryFinalSelfcheckPackageSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_delivery_submit_package_summary_verify" $stockAssistantDeliverySubmitPackageSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_real_gray_execution_manual_draft_summary_verify" $stockAssistantRealGrayExecutionManualDraftSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_real_gray_readonly_environment_snapshot_summary_verify" $stockAssistantRealGrayReadonlyEnvironmentSnapshotSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_first_real_gray_test_message_samples_summary_verify" $stockAssistantFirstRealGrayTestMessageSamplesSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_first_real_gray_test_review_template_summary_verify" $stockAssistantFirstRealGrayTestReviewTemplateSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_real_gray_human_release_confirmation_template_summary_verify" $stockAssistantRealGrayHumanReleaseConfirmationTemplateSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_real_gray_final_readonly_release_package_summary_verify" $stockAssistantRealGrayFinalReadonlyReleasePackageSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_real_gray_user_checklist_summary_verify" $stockAssistantRealGrayUserChecklistSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_real_gray_high_risk_operation_request_template_summary_verify" $stockAssistantRealGrayHighRiskOperationRequestTemplateSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_n8n_inactive_import_request_summary_verify" $stockAssistantN8nInactiveImportRequestSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_n8n_inactive_import_preexecution_readonly_check_summary_verify" $stockAssistantN8nInactiveImportPreexecutionReadonlyCheckSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_n8n_inactive_import_human_confirmation_receipt_template_summary_verify" $stockAssistantN8nInactiveImportHumanConfirmationReceiptTemplateSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_n8n_target_isolation_package_verify" $stockAssistantN8nTargetIsolationPackageVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_isolated_n8n_implementation_request_summary_verify" $stockAssistantIsolatedN8nImplementationRequestSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_isolated_n8n_startup_preflight_summary_verify" $stockAssistantIsolatedN8nStartupPreflightSummaryVerify.FullName "python" 180
$steps += Run-Step "isolated_n8n_controlled_start_config_summary_verify" $isolatedN8nControlledStartConfigSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_n8n_inactive_import_result_summary_verify" $stockAssistantN8nInactiveImportResultSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_gray_connectivity_preflight_summary_verify" $stockAssistantGrayConnectivityPreflightSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_local_gray_connectivity_drill_summary_verify" $stockAssistantLocalGrayConnectivityDrillSummaryVerify.FullName "python" 900
$steps += Run-Step "stock_assistant_real_wework_gray_gap_list_summary_verify" $stockAssistantRealWeworkGrayGapListSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_wework_controlled_send_gate_package_summary_verify" $stockAssistantWeworkControlledSendGatePackageSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_n8n_webhook_gray_entry_artifact_summary_verify" $stockAssistantN8nWebhookGrayEntryArtifactSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_n8n_webhook_gray_entry_inactive_import_result_summary_verify" $stockAssistantN8nWebhookGrayEntryInactiveImportResultSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_n8n_local_execution_loop_test_summary_verify" $stockAssistantN8nLocalExecutionLoopTestSummaryVerify.FullName "python" 300
$steps += Run-Step "stock_assistant_n8n_controlled_refresh_restart_request_package_summary_verify" $stockAssistantN8nControlledRefreshRestartRequestPackageSummaryVerify.FullName "python" 180
$steps += Run-Step "stock_assistant_n8n_controlled_refresh_restart_preexecution_snapshot_summary_verify" $stockAssistantN8nControlledRefreshRestartPreexecutionSnapshotSummaryVerify.FullName "python" 300
$steps += Run-Step "stock_assistant_n8n_post_refresh_webhook_gray_acceptance_plan_summary_verify" $stockAssistantN8nPostRefreshWebhookGrayAcceptancePlanSummaryVerify.FullName "python" 240
$steps += Run-Step "stock_assistant_delivery_usage_package_summary_verify" $stockAssistantDeliveryUsagePackageSummaryVerify.FullName "python" 240
$steps += Run-Step "stock_assistant_delivery_runtime_patrol_package_summary_verify" $stockAssistantDeliveryRuntimePatrolPackageSummaryVerify.FullName "python" 240
$steps += Run-Step "stock_assistant_local_delivery_functional_acceptance_package_summary_verify" $stockAssistantLocalDeliveryFunctionalAcceptancePackageSummaryVerify.FullName "python" 240
$steps += Run-Step "stock_assistant_local_service_refresh_request_package_summary_verify" $stockAssistantLocalServiceRefreshRequestPackageSummaryVerify.FullName "python" 180

$report = [pscustomobject]@{
    generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    root = $root
    summary = [pscustomobject]@{
        total = $steps.Count
        passed = ($steps | Where-Object { $_.ok }).Count
        failed = @($steps | Where-Object { -not $_.ok }).Count
    }
    steps = $steps
}

$report | ConvertTo-Json -Depth 8 | Set-Content -Path $reportPath -Encoding UTF8
Write-Output ($report.summary | ConvertTo-Json -Compress)
Write-Output $reportPath

if ($report.summary.failed -gt 0) {
    exit 1
}
exit 0
