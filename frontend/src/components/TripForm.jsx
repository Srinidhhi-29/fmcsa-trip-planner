import { useState } from "react";
import { Loader2, Navigation } from "lucide-react";

const initialValues = {
  current_location: " ",
  pickup_location: " ",
  dropoff_location: "",
  current_cycle_hours:0
};

export default function TripForm({ onSubmit, loading }) {
  const [values, setValues] = useState(initialValues);
  const [formError, setFormError] = useState("");

  function updateField(event) {
    const { name, value } = event.target;
    setValues((current) => ({
      ...current,
      [name]: name === "current_cycle_hours" ? Number(value) : value
    }));
  }

  function submit(event) {
    event.preventDefault();
    if (!values.current_location.trim() || !values.pickup_location.trim() || !values.dropoff_location.trim()) {
      setFormError("All locations are required.");
      return;
    }
    if (values.current_cycle_hours < 0 || values.current_cycle_hours > 70) {
      setFormError("Current cycle used must be between 0 and 70 hours.");
      return;
    }
    setFormError("");
    onSubmit(values);
  }

  return (
    <form className="trip-form" onSubmit={submit}>
      <div>
        <p className="section-kicker">Trip inputs</p>
        <h2>Build a compliant route</h2>
      </div>

          <input
        name="current_location"
        value={values.current_location}
        onChange={updateField}
        placeholder="Enter current location"
      />

      <input
        name="pickup_location"
        value={values.pickup_location}
        onChange={updateField}
        placeholder="Enter pickup location"
      />

      <input
        name="dropoff_location"
        value={values.dropoff_location}
        onChange={updateField}
        placeholder="Enter dropoff location"
      />

      <label>
        Current cycle used
        <input
          min="0"
          max="70"
          name="current_cycle_hours"
          required
          type="number"
          value={values.current_cycle_hours}
          onChange={updateField}
        />
      </label>

      {formError && <p className="form-error">{formError}</p>}

      <button type="submit" disabled={loading}>
        {loading ? <Loader2 className="spin" size={18} /> : <Navigation size={18} />}
        {loading ? "Planning" : "Plan trip"}
      </button>
    </form>
  );
}
