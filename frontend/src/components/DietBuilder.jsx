import { useEffect, useMemo, useState } from "react";
import api from "../api";
import "./DietBuilder.css";

const DAY_NAMES = [
  "Lunedì",
  "Martedì",
  "Mercoledì",
  "Giovedì",
  "Venerdì",
  "Sabato",
  "Domenica",
];

const FOOD_LIBRARY = {
  pollo: { kcal: 165, pro: 31, carb: 0, fat: 3.6 },
  riso: { kcal: 130, pro: 2.7, carb: 28, fat: 0.3 },
  avena: { kcal: 389, pro: 16.9, carb: 66.3, fat: 6.9 },
  banana: { kcal: 89, pro: 1.1, carb: 22.8, fat: 0.3 },
  yogurt: { kcal: 59, pro: 10, carb: 3.6, fat: 0.4 },
  salmone: { kcal: 208, pro: 20, carb: 0, fat: 13 },
};

function computeFoodMacros(foodName, grams) {
  const normalized = foodName.trim().toLowerCase();
  const foundKey = Object.keys(FOOD_LIBRARY).find((key) =>
    normalized.includes(key),
  );
  const base = foundKey
    ? FOOD_LIBRARY[foundKey]
    : { kcal: 120, pro: 8, carb: 12, fat: 4 };
  const ratio = Number(grams) / 100;
  return {
    kcal: base.kcal * ratio,
    pro: base.pro * ratio,
    carb: base.carb * ratio,
    fat: base.fat * ratio,
  };
}

function getBaseMacrosByFoodName(foodName) {
  return computeFoodMacros(foodName, 100);
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
  return DAY_NAMES.map(() => ({
    meals: [],
  }));
}

function DietBuilder() {
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

  const previewMacros = useMemo(() => {
    if (!selectedFood || Number(foodGrams) <= 0) {
      return { kcal: 0, pro: 0, carb: 0, fat: 0 };
    }
    return computeFoodMacros(selectedFood.nome, Number(foodGrams));
  }, [selectedFood, foodGrams]);

  const selectedBaseMacros = useMemo(() => {
    if (!selectedFood) {
      return null;
    }
    return getBaseMacrosByFoodName(selectedFood.nome);
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
        const response = await api.get("/alimenti/search", {
          params: { q: query },
        });
        if (cancelled) {
          return;
        }
        setSearchResults(response.data || []);
      } catch (_err) {
        if (cancelled) {
          return;
        }
        setSearchResults([]);
        setSearchError("Errore durante la ricerca alimenti.");
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

    const macros = computeFoodMacros(selectedFood.nome, Number(foodGrams));
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

  return (
    <section className="diet-builder">
      <header className="diet-builder__header">
        <div className="diet-builder__name">
          <label htmlFor="diet-name">Nome della Dieta</label>
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
      </header>

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
        {activeMeals.map((meal) => {
          const totals = mealTotals(meal);
          return (
            <article className="meal-accordion" key={meal.id}>
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
                <input
                  type="text"
                  className="meal-accordion__name-input"
                  value={meal.name}
                  onChange={(e) => handleMealNameChange(meal.id, e.target.value)}
                  onClick={(e) => e.stopPropagation()}
                  onKeyDown={(e) => e.stopPropagation()}
                  placeholder="Nome pasto"
                />
                <span>
                  {totals.kcal.toFixed(0)} kcal | P {totals.pro.toFixed(1)} | C{" "}
                  {totals.carb.toFixed(1)} | G {totals.fat.toFixed(1)}
                </span>
              </div>

              {meal.open && (
                <div className="meal-accordion__content">
                  {meal.foods.length === 0 ? (
                    <p className="muted">Nessun alimento inserito.</p>
                  ) : (
                    <ul>
                      {meal.foods.map((food) => (
                        <li key={food.id}>
                          {food.name} - {food.grams}g
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
          );
        })}

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
    </section>
  );
}

export default DietBuilder;
