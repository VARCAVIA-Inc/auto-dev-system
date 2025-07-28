package config

// BusinessMission corrisponde alla struttura di business_mission.yaml e funge da modello per il DNA dell'organismo.
type BusinessMission struct {
	MissionID   string        `yaml:"missionID"`
	Version     string        `yaml:"version"`
	MarketContext MarketContext `yaml:"marketContext"`
	Description string        `yaml:"description"`
	KPIs        []KPI         `yaml:"kpis"`
	Constraints Constraints   `yaml:"constraints"`
}

// MarketContext definisce il contesto di mercato in cui opera la missione.
type MarketContext struct {
	TargetMarketSegment string `yaml:"targetMarketSegment"`
	CompetitiveAdvantage string `yaml:"competitiveAdvantage"`
}

// KPI (Key Performance Indicator) definisce una metrica di successo per la missione.
type KPI struct {
	Name   string `yaml:"name"`
	Target string `yaml:"target"`
	Query  string `yaml:"query"`
}

// Constraints definisce i limiti operativi e di budget per la missione.
type Constraints struct {
	Budget Budget `yaml:"budget"`
}

// Budget specifica i vincoli finanziari.
type Budget struct {
	MonthlyAmountEUR int    `yaml:"monthlyAmountEUR"`
	Currency         string `yaml:"currency"`
}