string baseFilePath = "C:\\Users\\Felix\\Documents\\Ia trackmania\\Trackmania\\Db\\vehicle_inputs_";
string filePath = ""; 
bool isRaceStarted = false;  
bool isRaceFinished = false;
uint64 raceStartTime = 0;  
bool retireHandled = false;
uint preCPIdx = 0;  // Pour suivre l'index du dernier checkpoint
int cpCount = 0;    // Pour compter les CP dans l'ordre
int startTime = 0;  // Pour calculer le vrai temps de course

bool DetectInGame() {
    auto playground = cast<CSmArenaClient>(GetApp().CurrentPlayground);
    if (playground is null
        || playground.Arena is null
        || playground.Map is null
        || playground.GameTerminals.Length <= 0
        || (
            playground.GameTerminals[0].UISequence_Current != CGamePlaygroundUIConfig::EUISequence::Playing
            && playground.GameTerminals[0].UISequence_Current != CGamePlaygroundUIConfig::EUISequence::Finish
        )
        || cast<CSmPlayer>(playground.GameTerminals[0].GUIPlayer) is null) {
        return false;
    }

    auto player = cast<CSmPlayer>(playground.GameTerminals[0].GUIPlayer);
    if (player is null || player.CurrentLaunchedRespawnLandmarkIndex == uint(-1)) {
        return false;
    }
    
    return true;
}

void Main() {
    print("🚀 MyPlugin | Vehicle Input Logger actif !");
}

void Render() { 
    if (!DetectInGame()) return;

    auto vis = VehicleState::ViewingPlayerState();
    if (vis is null) return;

    float accel = vis.InputGasPedal;
    float brake = vis.InputBrakePedal;
    float steer = vis.InputSteer;
    float speed = vis.FrontSpeed;
    vec3 pos = vis.Position;
    uint64 currentTime = Time::Now;

    CGameCtnApp@ app = GetApp();
    auto playground = cast<CSmArenaClient>(app.CurrentPlayground);
    if (playground is null) return;
    
    if (playground.GameTerminals.Length > 0) {
        auto terminal = playground.GameTerminals[0];
        auto player = cast<CSmPlayer>(terminal.GUIPlayer);
        
        // Détection du restart/début de course
        if (player !is null) {
            auto scriptPlayer = cast<CSmScriptPlayer@>(player.ScriptAPI);
            auto post = scriptPlayer.Post;
            
            // Détection du restart
            if (!retireHandled && post == CSmScriptPlayer::EPost::Char) {
                print("🔄 Restart détecté !");
                retireHandled = true;
                isRaceStarted = false;
                isRaceFinished = false;
                filePath = "";
                preCPIdx = 0;
                cpCount = 0;
                startTime = 0;
            } 
            // Détection du début de course
            else if (retireHandled && post == CSmScriptPlayer::EPost::CarDriver) {
                isRaceStarted = true;
                isRaceFinished = false;
                raceStartTime = currentTime;
                retireHandled = false;
                preCPIdx = 0;
                cpCount = 0;
                startTime = Time::Now;

                filePath = baseFilePath + raceStartTime + ".csv";
                IO::File f(filePath, IO::FileMode::Write);
                f.WriteLine("Timestamp,Accel,Brake,Steer,Speed,PosX,PosY,PosZ,CurrentCP,RaceTime");
                f.Close();

                print("🏁 Nouvelle course détectée ! Enregistrement dans : " + filePath);
            }
        }

        // Détection de fin de course
        if (terminal.UISequence_Current == CGamePlaygroundUIConfig::EUISequence::Finish && !isRaceFinished) {
            print("🏁 Course terminée !");
            isRaceFinished = true;
            isRaceStarted = false;
            filePath = "";
            preCPIdx = 0;
            cpCount = 0;
            startTime = 0;
        }

        // Enregistrement des inputs et données checkpoints
        if (isRaceStarted && !isRaceFinished && filePath != "" && player !is null) {
            auto scriptPlayer = cast<CSmScriptPlayer@>(player.ScriptAPI);
            
            // Calcul du temps de course
            int raceTime = 0;
            if (startTime > 0) {
                raceTime = Time::Now - startTime;
            }
            
            // Détection des checkpoints façon Split Speeds
            MwFastBuffer<CGameScriptMapLandmark@> landmarks = playground.Arena.MapLandmarks;
            if (preCPIdx != player.CurrentLaunchedRespawnLandmarkIndex && landmarks.Length > player.CurrentLaunchedRespawnLandmarkIndex) {
                preCPIdx = player.CurrentLaunchedRespawnLandmarkIndex;
                auto landmark = landmarks[preCPIdx];
                
                if (landmark.Waypoint !is null) {
                    if (landmark.Waypoint.IsFinish || landmark.Waypoint.IsMultiLap) {
                        print("🏁 Ligne d'arrivée ! Temps : " + (raceTime / 1000.0f) + "s");
                    } else {
                        cpCount++;
                        print("⭐ CP " + cpCount + " passé ! Temps : " + (raceTime / 1000.0f) + "s");
                    }
                }
            }

            IO::File f(filePath, IO::FileMode::Append);
            f.WriteLine(
                currentTime + "," +
                accel + "," + 
                brake + "," + 
                steer + "," + 
                speed + "," + 
                pos.x + "," + 
                pos.y + "," + 
                pos.z + "," +
                cpCount + "," +
                raceTime
            );
            f.Close();
        }
    }
}