"use client"
// import Image from "next/image";
// import POI_FORM from "./components/Add_poi_form";
import Show_prev_POIs from "./components/Show_all_pois";
import Crawl_sites from "./components/Crawl_sites";
import { useState } from "react";

export default function Home() {

  const [poi_id, set_poi_id] = useState(null);

  return (
    <div className=" pl-8 divide-x-[1px] divide-primary flex gap-4">
        <Show_prev_POIs poi_id={poi_id} set_poi_id={set_poi_id} />
        <Crawl_sites poi_id={poi_id} /> 
    </div>
  );
}
