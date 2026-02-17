import { useEffect, useMemo, useState } from "react";
import { DragDropContext, Draggable, Droppable } from "@hello-pangea/dnd";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { useNavigate, useParams } from "react-router-dom";
import api, {
  aggiornaDietaCompleta,
  calcolaMicroGiornalieri,
  salvaDietaCompleta,
} from "../api";
import "./DietBuilder.css";

const DAY_NAMES = [
  "Lunedi",
  "Martedi",
  "Mercoledi",
  "Giovedi",
  "Venerdi",
  "Sabato",
  "Domenica",
];

function toFloatValue(value) {
  if (value === null || value === undefined) {
    return 0;
  }
  const raw = String(value).trim().toLowerCase().replace(",", ".");
  if (!raw || raw === "tr") {
    return 0;
  }
  const parsed = Number(raw);
  return Number.isNaN(parsed) ? 0 : parsed;
}

function computeFoodMacros(food, grams) {
  const base = {
    kcal: toFloatValue(food.kcal),
    pro: toFloatValue(food.proteine),
    carb: toFloatValue(food.carboidrati),
    fat: toFloatValue(food.grassi),
  };
  const ratio = Number(grams) / 100;
  return {
    kcal: base.kcal * ratio,
    pro: base.pro * ratio,
    carb: base.carb * ratio,
    fat: base.fat * ratio,
  };
}

function mealTotals(meal) {
  return meal.foods.reduce(
    (acc, food) => ({
      kcal: acc.kcal + food.kcal,
      pro: acc.pro + food.pro,
      carb: acc.carb + food.carb,
      fat: acc.fat + food.fat,
    }),
    { kcal: 0, pro: 0, carb: 0, fat: 0 },
  );
}

function buildInitialWeekPlan() {
  return DAY_NAMES.map(() => ({ meals: [] }));
}

function DietBuilder() {
  const navigate = useNavigate();
  const { id } = useParams();

  const [dietName, setDietName] = useState("Dieta Ricomposizione");
  const [activeDay, setActiveDay] = useState(0);
  const [weekPlan, setWeekPlan] = useState(buildInitialWeekPlan);
  const [modalOpen, setModalOpen] = useState(false);
  const [targetMealId, setTargetMealId] = useState(null);
  const [foodSearch, setFoodSearch] = useState("");
  const [foodGrams, setFoodGrams] = useState(100);
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedFood, setSelectedFood] = useState(null);
  const [searchError, setSearchError] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [isLoading, setIsLoading] = useState(Boolean(id));
  const [saveError, setSaveError] = useState("");
  const [showMicroOverlay, setShowMicroOverlay] = useState(false);
  const [microData, setMicroData] = useState(null);
  const [isMicroLoading, setIsMicroLoading] = useState(false);

  const activeMeals = weekPlan[activeDay].meals;

  const dailyTotals = useMemo(() => {
    return activeMeals.reduce(
      (acc, meal) => {
        const totals = mealTotals(meal);
        return {
          kcal: acc.kcal + totals.kcal,
          pro: acc.pro + totals.pro,
          carb: acc.carb + totals.carb,
          fat: acc.fat + totals.fat,
        };
      },
      { kcal: 0, pro: 0, carb: 0, fat: 0 },
    );
  }, [activeMeals]);

  const macroData = [
    { name: "Proteine", value: Number(dailyTotals.pro.toFixed(1)), color: "#3b82f6" },
    { name: "Carboidrati", value: Number(dailyTotals.carb.toFixed(1)), color: "#ef4444" },
    { name: "Grassi", value: Number(dailyTotals.fat.toFixed(1)), color: "#eab308" },
  ];
  const hasMacroData = macroData.some((item) => item.value > 0);

  const previewMacros = useMemo(() => {
    if (!selectedFood || Number(foodGrams) <= 0) {
      return { kcal: 0, pro: 0, carb: 0, fat: 0 };
    }
    return computeFoodMacros(selectedFood, Number(foodGrams));
  }, [selectedFood, foodGrams]);

  const selectedBaseMacros = useMemo(() => {
    if (!selectedFood) {
      return null;
    }
    return {
      kcal: toFloatValue(selectedFood.kcal),
      pro: toFloatValue(selectedFood.proteine),
      carb: toFloatValue(selectedFood.carboidrati),
      fat: toFloatValue(selectedFood.grassi),
    };
  }, [selectedFood]);

  useEffect(() => {
    if (!modalOpen) {
      return;
    }
    const query = foodSearch.trim();
    if (query.length < 2) {
      setSearchResults([]);
      setIsSearching(false);
      setSearchError("");
      return;
    }

    let cancelled = false;
    const debounceTimer = setTimeout(async () => {
      setIsSearching(true);
      setSearchError("");
      try {
        const response = await api.get("/alimenti/search", { params: { q: query } });
        if (!cancelled) {
          setSearchResults(response.data || []);
        }
      } catch (_err) {
        if (!cancelled) {
          setSearchResults([]);
          setSearchError("Errore durante la ricerca alimenti.");
        }
      } finally {
        if (!cancelled) {
          setIsSearching(false);
        }
      }
    }, 300);

    return () => {
      cancelled = true;
      clearTimeout(debounceTimer);
    };
  }, [foodSearch, modalOpen]);

  useEffect(() => {
    if (!id) {
      setIsLoading(false);
      return;
    }

    let cancelled = false;
    const loadDieta = async () => {
      try {
        setIsLoading(true);
        const response = await api.get(`/diete/${id}/completa`);
        if (!cancelled) {
          setDietName(response.data?.nome || "Dieta");
          setWeekPlan(response.data?.week_plan || buildInitialWeekPlan());
        }
      } catch (_err) {
        if (!cancelled) {
          setDietName("Dieta Ricomposizione");
          setWeekPlan(buildInitialWeekPlan());
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    loadDieta();
    return () => {
      cancelled = true;
    };
  }, [id]);

  const toggleMeal = (mealId) => {
    setWeekPlan((prev) =>
      prev.map((day, index) =>
        index !== activeDay
          ? day
          : {
              ...day,
              meals: day.meals.map((meal) =>
                meal.id === mealId ? { ...meal, open: !meal.open } : meal,
              ),
            },
      ),
    );
  };

  const handleAddMeal = () => {
    setWeekPlan((prev) =>
      prev.map((day, index) =>
        index !== activeDay
          ? day
          : {
              ...day,
              meals: [
                ...day.meals,
                {
                  id: Math.random().toString(36).slice(2),
                  name: `Pasto ${day.meals.length + 1}`,
                  open: true,
                  foods: [],
                },
              ],
            },
      ),
    );
  };

  const handleMealNameChange = (mealId, newName) => {
    setWeekPlan((prev) =>
      prev.map((day, index) =>
        index !== activeDay
          ? day
          : {
              ...day,
              meals: day.meals.map((meal) =>
                meal.id === mealId ? { ...meal, name: newName } : meal,
              ),
            },
      ),
    );
  };

  const openAddFoodModal = (mealId) => {
    setTargetMealId(mealId);
    setFoodSearch("");
    setFoodGrams(100);
    setSearchResults([]);
    setSelectedFood(null);
    setSearchError("");
    setModalOpen(true);
  };

  const handleSaveFood = () => {
    if (!selectedFood || Number(foodGrams) <= 0 || !targetMealId) {
      return;
    }
    const macros = computeFoodMacros(selectedFood, Number(foodGrams));
    const newFood = {
      id: Math.random().toString(36).slice(2),
      codice_alimento: selectedFood.codice_alimento,
      name: selectedFood.nome,
      grams: Number(foodGrams),
      ...macros,
    };

    setWeekPlan((prev) =>
      prev.map((day, index) =>
        index !== activeDay
          ? day
          : {
              ...day,
              meals: day.meals.map((meal) =>
                meal.id === targetMealId
                  ? { ...meal, foods: [...meal.foods, newFood], open: true }
                  : meal,
              ),
            },
      ),
    );
    setModalOpen(false);
  };

  const handleSelectFood = (food) => {
    setSelectedFood(food);
    setFoodSearch("");
    setSearchResults([]);
  };

  const rimuoviAlimento = (pastoId, indiceAlimento) => {
    setWeekPlan((prev) =>
      prev.map((day, index) =>
        index !== activeDay
          ? day
          : {
              ...day,
              meals: day.meals.map((meal) =>
                meal.id !== pastoId
                  ? meal
                  : {
                      ...meal,
                      foods: meal.foods.filter((_, foodIndex) => foodIndex !== indiceAlimento),
                    },
              ),
            },
      ),
    );
  };

  const handleDragEnd = (result) => {
    const { source, destination } = result;
    if (!destination) {
      return;
    }
    if (source.index === destination.index) {
      return;
    }

    const reorderedMeals = Array.from(activeMeals);
    const [movedItem] = reorderedMeals.splice(source.index, 1);
    reorderedMeals.splice(destination.index, 0, movedItem);

    setWeekPlan((prev) =>
      prev.map((day, index) =>
        index !== activeDay
          ? day
          : {
              ...day,
              meals: reorderedMeals,
            },
      ),
    );
  };

  const handleSalvaDieta = async () => {
    setSaveError("");
    setIsSaved(false);

    const pastiPayload = [];
    weekPlan.forEach((day, dayIndex) => {
      day.meals.forEach((meal, mealIndex) => {
        const alimenti = meal.foods
          .filter((food) => food.codice_alimento && Number(food.grams) > 0)
          .map((food) => ({
            codice_alimento: food.codice_alimento,
            grammi: Math.round(Number(food.grams)),
          }));

        pastiPayload.push({
          nome_pasto: meal.name?.trim() || "Pasto",
          giorno_settimana: dayIndex + 1,
          ordine: mealIndex + 1,
          alimenti,
        });
      });
    });

    const payload = { nome: dietName.trim() || "Nuova Dieta", pasti: pastiPayload };

    try {
      setIsSaving(true);
      if (id) {
        await aggiornaDietaCompleta(id, payload);
      } else {
        await salvaDietaCompleta(payload);
      }
      setIsSaved(true);
      setTimeout(() => navigate("/dashboard"), 2000);
    } catch (_err) {
      setSaveError("Errore durante il salvataggio della dieta");
    } finally {
      setIsSaving(false);
    }
  };

  const openMicroOverlay = async () => {
    const alimenti = activeMeals.flatMap((meal) =>
      meal.foods
        .filter((food) => food.codice_alimento && Number(food.grams) > 0)
        .map((food) => ({
          codice_alimento: food.codice_alimento,
          grammi: Number(food.grams),
        })),
    );

    if (alimenti.length === 0) {
      alert("Nessun alimento in questo giorno");
      return;
    }

    setShowMicroOverlay(true);
    setIsMicroLoading(true);
    setMicroData(null);

    try {
      const response = await calcolaMicroGiornalieri(alimenti);
      setMicroData(response.data || {});
    } catch (_err) {
      setMicroData(null);
      alert("Errore durante il calcolo dei micronutrienti");
    } finally {
      setIsMicroLoading(false);
    }
  };

  if (isLoading) {
    return (
      <section className="diet-builder">
        <div className="diet-builder__loading">Caricamento in corso...</div>
      </section>
    );
  }

  return (
    <section className="diet-builder">
      <header className="diet-builder__header">
        <div className="diet-builder__header-left">
          <div className="diet-builder__name">
            <div className="diet-builder__title-row">
              <label htmlFor="diet-name">Nome della Dieta</label>
              <button
                type="button"
                className="btn-primary btn-save-diet"
                onClick={handleSalvaDieta}
                disabled={isSaving || isSaved}
              >
                {isSaving ? "Salvataggio..." : isSaved ? "✅ Salvato!" : "Salva Dieta"}
              </button>
            </div>
            <input
              id="diet-name"
              value={dietName}
              onChange={(e) => setDietName(e.target.value)}
              placeholder="Inserisci un nome"
            />
          </div>
          <div className="diet-builder__totals">
            <span>Kcal: {dailyTotals.kcal.toFixed(0)}</span>
            <span>Pro: {dailyTotals.pro.toFixed(1)}g</span>
            <span>Carbo: {dailyTotals.carb.toFixed(1)}g</span>
            <span>Grassi: {dailyTotals.fat.toFixed(1)}g</span>
          </div>
        </div>
        <div className="diet-builder__chart-wrap">
          {hasMacroData ? (
            <div
              className="diet-builder__chart-box diet-builder__chart-box--clickable"
              role="button"
              tabIndex={0}
              onClick={openMicroOverlay}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  openMicroOverlay();
                }
              }}
            >
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={macroData}
                    innerRadius={50}
                    outerRadius={70}
                    paddingAngle={5}
                    dataKey="value"
                    stroke="none"
                  >
                    {macroData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => `${value} g`} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div
              className="diet-builder__chart-empty diet-builder__chart-box--clickable"
              onClick={openMicroOverlay}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  openMicroOverlay();
                }
              }}
              role="button"
              tabIndex={0}
            >
              Nessun dato
            </div>
          )}
        </div>
      </header>
      {saveError && <p className="diet-builder__save-error">{saveError}</p>}

      <nav className="diet-builder__tabs">
        {DAY_NAMES.map((day, index) => (
          <button
            key={day}
            type="button"
            className={index === activeDay ? "is-active" : ""}
            onClick={() => setActiveDay(index)}
          >
            {day}
          </button>
        ))}
      </nav>

      <div className="diet-builder__body">
        <DragDropContext onDragEnd={handleDragEnd}>
          <Droppable droppableId="meals-list">
            {(droppableProvided) => (
              <div
                className="meals-droppable"
                ref={droppableProvided.innerRef}
                {...droppableProvided.droppableProps}
              >
                {activeMeals.map((meal, index) => {
                  const totals = mealTotals(meal);
                  return (
                    <Draggable key={meal.id} draggableId={String(meal.id)} index={index}>
                      {(draggableProvided) => (
                        <article
                          className="meal-accordion"
                          ref={draggableProvided.innerRef}
                          {...draggableProvided.draggableProps}
                        >
                          <div
                            className="meal-accordion__head"
                            role="button"
                            tabIndex={0}
                            onClick={() => toggleMeal(meal.id)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter" || e.key === " ") {
                                e.preventDefault();
                                toggleMeal(meal.id);
                              }
                            }}
                          >
                            <div className="meal-accordion__head-content">
                              <div className="meal-accordion__title-group">
                                <span
                                  className="meal-drag-handle"
                                  {...draggableProvided.dragHandleProps}
                                  onClick={(e) => e.stopPropagation()}
                                  onKeyDown={(e) => e.stopPropagation()}
                                  title="Trascina per riordinare"
                                >
                                  ::
                                </span>
                                <input
                                  type="text"
                                  className="meal-accordion__name-input"
                                  value={meal.name}
                                  onChange={(e) => handleMealNameChange(meal.id, e.target.value)}
                                  onClick={(e) => e.stopPropagation()}
                                  onKeyDown={(e) => e.stopPropagation()}
                                  placeholder="Nome pasto"
                                />
                              </div>
                              <div className="meal-accordion__macros">
                                <span className="macro-pill macro-pill--kcal">
                                  Kcal {totals.kcal.toFixed(0)}
                                </span>
                                <span className="macro-pill macro-pill--pro">
                                  P {totals.pro.toFixed(1)}
                                </span>
                                <span className="macro-pill macro-pill--carb">
                                  C {totals.carb.toFixed(1)}
                                </span>
                                <span className="macro-pill macro-pill--fat">
                                  G {totals.fat.toFixed(1)}
                                </span>
                              </div>
                            </div>
                          </div>

                          {meal.open && (
                            <div className="meal-accordion__content">
                              {meal.foods.length === 0 ? (
                                <p className="muted">Nessun alimento inserito.</p>
                              ) : (
                                <ul className="foods-list">
                                  {meal.foods.map((food, foodIndex) => (
                                    <li key={food.id} className="food-card">
                                      <div className="food-card__left">
                                        <strong>{food.name}</strong>
                                        <span>Quantita: {food.grams} g</span>
                                      </div>
                                      <div className="food-card__center">
                                        <span>Kcal {food.kcal.toFixed(0)}</span>
                                        <span>P {food.pro.toFixed(1)}</span>
                                        <span>C {food.carb.toFixed(1)}</span>
                                        <span>G {food.fat.toFixed(1)}</span>
                                      </div>
                                      <div className="food-card__right">
                                        <button
                                          type="button"
                                          className="btn-delete"
                                          onClick={() => rimuoviAlimento(meal.id, foodIndex)}
                                        >
                                          Elimina
                                        </button>
                                      </div>
                                    </li>
                                  ))}
                                </ul>
                              )}

                              <button
                                type="button"
                                className="btn-secondary"
                                onClick={() => openAddFoodModal(meal.id)}
                              >
                                Aggiungi Alimento
                              </button>
                            </div>
                          )}
                        </article>
                      )}
                    </Draggable>
                  );
                })}
                {droppableProvided.placeholder}
              </div>
            )}
          </Droppable>
        </DragDropContext>

        <button type="button" className="btn-primary" onClick={handleAddMeal}>
          Aggiungi Pasto
        </button>
      </div>

      {modalOpen && (
        <div className="modal-overlay" role="presentation">
          <div className="modal">
            <h3>Aggiungi Alimento</h3>
            <input
              type="text"
              placeholder="Cerca alimento"
              value={foodSearch}
              onChange={(e) => {
                setFoodSearch(e.target.value);
                setSelectedFood(null);
              }}
            />
            {isSearching && <p className="muted">Ricerca in corso...</p>}
            {searchError && <p className="modal-error">{searchError}</p>}
            {!isSearching && searchResults.length > 0 && (
              <ul className="search-results">
                {searchResults.map((food) => (
                  <li key={food.codice_alimento}>
                    <button type="button" onClick={() => handleSelectFood(food)}>
                      <strong>{food.nome}</strong>
                      <span>{food.categoria || "Categoria non disponibile"}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}

            {selectedFood && selectedBaseMacros && (
              <div className="nutrition-preview">
                <p className="nutrition-preview__title">
                  Selezionato: <strong>{selectedFood.nome}</strong>
                </p>
                <p className="nutrition-preview__base">
                  Valori base (100g): Kcal {selectedBaseMacros.kcal.toFixed(0)}
                  {" | "}P {selectedBaseMacros.pro.toFixed(1)}
                  {" | "}C {selectedBaseMacros.carb.toFixed(1)}
                  {" | "}G {selectedBaseMacros.fat.toFixed(1)}
                </p>
              </div>
            )}

            <input
              type="number"
              min="1"
              placeholder="Grammi"
              value={foodGrams}
              onChange={(e) => setFoodGrams(e.target.value)}
            />

            <div className="nutrition-preview">
              <p className="nutrition-preview__title">Anteprima porzione</p>
              <p>
                Kcal {previewMacros.kcal.toFixed(0)} | Pro {previewMacros.pro.toFixed(1)}g |
                Carbo {previewMacros.carb.toFixed(1)}g | Grassi {previewMacros.fat.toFixed(1)}g
              </p>
            </div>

            <div className="modal__actions">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setModalOpen(false)}
              >
                Annulla
              </button>
              <button
                type="button"
                className="btn-primary"
                onClick={handleSaveFood}
                disabled={!selectedFood || Number(foodGrams) <= 0}
              >
                Aggiungi all'elenco
              </button>
            </div>
          </div>
        </div>
      )}

      {showMicroOverlay && (
        <div className="diet-builder__micro-overlay" role="dialog" aria-modal="true">
          <div className="diet-builder__micro-header">
            <h2>Analisi Micronutrienti - {DAY_NAMES[activeDay]}</h2>
            <button
              type="button"
              className="diet-builder__micro-close"
              onClick={() => setShowMicroOverlay(false)}
            >
              Chiudi (X)
            </button>
          </div>

          {isMicroLoading && (
            <div className="diet-builder__micro-loading">
              <div className="diet-builder__spinner" aria-hidden="true" />
              <p>Calcolo micronutrienti in corso...</p>
            </div>
          )}

          {!isMicroLoading && microData && (
            <div className="diet-builder__micro-grid">
              {Object.keys(microData)
                .sort((a, b) => a.localeCompare(b))
                .map((nutriente) => (
                  <div key={nutriente} className="diet-builder__micro-card">
                    <span className="diet-builder__micro-name">{nutriente}</span>
                    <strong className="diet-builder__micro-value">
                      {Number(microData[nutriente] || 0).toFixed(2)}
                    </strong>
                  </div>
                ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export default DietBuilder;
